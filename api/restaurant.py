import shutil
from fastapi import UploadFile, File, Body
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text, or_
from sqlalchemy.orm import Session, joinedload
from database.connection import get_db

# 맨 윗부분 import 모여있는 곳에 추가
from api.user import get_current_user
from database.orm import User, Restaurant, Review, ReviewLike, Follow

# 👇 [수정] 님이 만든 파일(request.py, response.py)에서 클래스 가져오기
from schema.request import RestaurantCreate, CreateReviewRequest, UpdateReviewRequest, CreateCollectionRequest
from schema.response import RestaurantResponse, ReviewResponse, RankingResponse

# DB 저장 함수
from database.repository import (
    create_restaurant, delete_restaurant, get_review_king, get_popular_star,
    get_review_detail, get_reviews_by_restaurant_id, create_bookmark, delete_bookmark, get_user_bookmark,
    get_restaurant_by_name, create_review, update_review, delete_review, get_user_reviews, create_collection,
    get_all_collections, delete_collection, create_comment, get_comments_by_review, delete_comment, get_user_followers,
    get_user_following
)

# 네이버 검색 함수
from service.naver_collector import search_restaurants_by_location

router = APIRouter(prefix="/restaurants")

# 리뷰 데이터에 닉네임을 찾아 붙여주는 함수
def format_reviews(session: Session, reviews):
    result = []
    for r in reviews:
        user = session.query(User).filter(User.id == r.user_id).first()
        result.append({
            "id" : r.id,
            "content" : r.content,
            "rating": r.rating,
            "view_count" : r.view_count,
            "user_id": r.user_id,
            "nickname" : user.nickname if user else "익명",
            "restaurant_id" : r.restaurant_id,
            "created_at" : r.created_at,
            "image_url" : r.image_url
        })
    return result

# ==========================================
# 1. 맛집 저장 API (POST)
# 프론트엔드에서 [저장] 버튼 누르면 실행됨
# 가게를 찜하면 내 포스트잇이 붙는다
# ==========================================
@router.post("", status_code=201)
def save_restaurant_api(
        request: RestaurantCreate,  # 👈 여기 이름을 RestaurantCreate로 맞췄습니다
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # DB에 이 식당이 등록되어 있는지 확인
    restaurant = get_restaurant_by_name(session, request.name)
    # 없다면 새로 생성
    if not restaurant:
        # DB에 저장하는 함수 호출
        # (repository의 함수도 이 스키마를 받도록 되어 있어야 합니다)
        restaurant = create_restaurant(session=session, request=request)

    create_bookmark(session, current_user.id, restaurant.id)

    # 결과 반환
    return {"message": f"{restaurant.name} 찜 성공!"}

# ==========================================
# 2. 맛집 검색 API (GET)
# 프론트엔드에서 [검색] 버튼 누르면 실행됨 (DB 저장 X)
# ==========================================
@router.get("/search")
def search_naver_handler(query: str):
    # 네이버 검색 서비스 호출
    results = search_restaurants_by_location(query)
    return results

# 찜 목록 가져오기 (내 찜 목록 보기)
# RestaurantResponse 양식으로 리스트를 만들어서 줌
@router.get("", response_model=List[RestaurantResponse])
def get_restaurants_api(
        user_id: Optional[int] = Query(None), session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 파라미터로 user_id가 들어오면 그 사람껄, 없으면 로그인한 내 목록을 타켓으로 설정
    target_id = user_id if user_id is not None else current_user.id
    return get_user_bookmark(session, target_id)

# 찜 취소하기
@router.delete("/{restaurant_id}", status_code=204)
def delete_restaurant_api(
        restaurant_id: int,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 내 아이디로 된 찜 기록만 삭제
    delete_bookmark(session, current_user.id, restaurant_id)
    return

# 리뷰 등록하기
@router.post("/{restaurant_id}/reviews", status_code=201, response_model = ReviewResponse)
def register_review(
     restaurant_id: int,
     request: CreateReviewRequest, # 손님이 보낸 리뷰 내용
     current_user: User = Depends(get_current_user),
     session: Session = Depends(get_db)
):
    request.restaurant_id = restaurant_id
    return create_review(session, current_user.id, request)

# 내 리뷰만 모아보기 /my/reviews 주소로 찾아갔더니 숫자가 들어가야 할 자리에 my라는 글자가 옴
# 숫자가 아니라 에러가 뜸
@router.get("/my/reviews", response_model=List[ReviewResponse])
def get_my_reviews(
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
   reviews =  get_user_reviews(session, current_user.id)
   return format_reviews(session, reviews)


# 특정 가게 리뷰 보기
# .all() 이라고 명령하면 DB에서 데이터를 꺼낸 다음 알아서 리스트에 담아줌
# 이미 꽉 찬 리스트를 뱉어내고 있기 때문에 빈 상자를 만들 필요 없이 그대로 전달함
@router.get("/{restaurant_id}/reviews", response_model=List[ReviewResponse])
def get_reviews(
        restaurant_id: int, session: Session = Depends(get_db)
):
    reviews = get_reviews_by_restaurant_id(session, restaurant_id)
    return format_reviews(session,reviews)



# 리뷰 1개 상세 보기 (여기를 호출해야 조회수가 오름)
@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review_detail_api(
        review_id: int,
        session: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    # repository의 함수 호출 (여기서 조회수 +1 됨)
    review = get_review_detail(session, review_id, current_user.id)

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return review

# 명예의 전당
# 반드시 List에 담아서 줘야함 rankings = []를 구해서 펼쳐 놓고 append를 함
# 낱개로 들고 있어서 빈 박스를 가져와 append해서 줘야함
@router.get("/rankings", response_model=List[RankingResponse])
def get_user_rankings_api(session: Session = Depends(get_db)):
    king = get_review_king(session)
    star = get_popular_star(session)

    rankings = []

    if king:
        user_obj, count = king # 첫 번째 칸 : 모든 정보 / 두 번째 칸 : 숫자
        rankings.append({
            "user_id": user_obj.id,
            "title" : "리뷰 왕",
            "nickname" : user_obj.nickname,
            "score": count,
            "message" : f"총 {count}개의 리뷰를 작성했어요!"
        })

    if star: # 만약 star 데이터가 존재하고 조회수가 0이면 안 되기 때문에 최소 1번 이상은 읽혔을 때 랭킹에 올림
        user_obj = star[0]
        total_views = star[1]

        if total_views is not None and total_views > 0:
           rankings.append({
             "user_id": user_obj.id,
             "title" : "인기 스타",
             "nickname" : user_obj.nickname,
             "score": int(total_views),
             "message" : f"작성한 리뷰가 총 {int(total_views)}번 읽혔어요!"
           })

    return rankings

# 리뷰 수정
@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review_api(
        review_id: int,
        request: UpdateReviewRequest,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)

):
    review = update_review(session, review_id, current_user.id, request.content, request.rating)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

# 리뷰 삭제
@router.delete("/reviews/{review_id}", status_code=204)
def delete_review_api(
        review_id: int,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    success = delete_review(session, review_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    return

# 특정 유저가 쓴 리뷰 모아보기
@router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
def get_user_reviews_api(
        user_id: int,
        session: Session = Depends(get_db)
):
    reviews = get_user_reviews(session, user_id)
    return format_reviews(session, reviews)

# 사진 업로드 API (리뷰 쓰기 전 사진 먼저 저장)
@router.post("/reviews/upload")
def upload_review_image(file: UploadFile = File(...)):
    # 사진을 서버의 static/uploads 폴더에 저장
    file_path = f"static/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"image_url": f"/{file_path}"}


# 커뮤니티 피드 API 만들기
# 사진 중심 커뮤니티 피드
# 최신 리뷰 + 식당 정보 + 유저 닉네임

@router.get("/community/feed")
def get_community_feed_api(
        category: Optional[str] = None,
        region: Optional[str] = None,
        sort_by: Optional[str] = None,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    query = session.query(Review).join(Restaurant)
    if category:
        query = query.filter(
            or_(Restaurant.category.contains(category), Restaurant.name.contains(category))
        )

    if region:
        query = query.filter(Restaurant.address.contains(region))

    # .join() (Inner Join = 교집합) 양쪽 테이블에 데이터가 있는 것만 가져옴
    # 리뷰에 좋아요가 없다면 피드에서 없앰
    # .outerjoin() (Left Outer Join = 기준점 살리기)
    # 데이터가 없더라고 리뷰는 살려둠
    if sort_by == "likes":
        query = query.outerjoin(ReviewLike, Review.id == ReviewLike.review_id).group_by(Review.id).order_by(func.count(ReviewLike.id).desc())

    else:
        query = query.order_by(Review.id.desc())
    # 가장 최근에 작성된 리뷰 20개를 가져옴
    recent_reviews = query.options(joinedload(Review.user), joinedload(Review.restaurant)) \
        .order_by(Review.id.desc()).limit(20).all()
    feed_list = []
    for r in recent_reviews:
        user = session.query(User).filter(User.id == r.user_id).first()
        rest = session.query(Restaurant).filter(Restaurant.id == r.restaurant_id).first()

        l_count = session.query(ReviewLike).filter(ReviewLike.review_id == r.id).count()

        # 내가 좋아요를 눌렀는지?
        i_liked = session.query(ReviewLike).filter(
            ReviewLike.user_id == current_user.id,
            ReviewLike.review_id == r.id).first() is not None

        # 내가 이 사람을 팔로우 했나?
        is_following = session.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == r.user_id
        ).first() is not None

        if user and rest:
            feed_list.append({
                "review_id": r.id,
                "user_id" : user.id,
                "nickname": user.nickname,
                "restaurant_name": rest.name,
                "address": rest.address,
                "category": rest.category,
                "content": r.content,
                "rating": r.rating,
                "image_url":r.image_url,
                "like_count": l_count,
                "view_count": r.view_count,
                "is_liked": i_liked,
                "is_followed": is_following

            })

    return feed_list

# 리뷰 좋아요 누르기
@router.post("/reviews/{review_id}/like")
def like_review_api(
        review_id: int,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    existing = session.query(ReviewLike).filter_by(user_id=current_user.id, review_id=review_id).first()
    if existing:
        # 이미 있다면 좋아요 취소
        session.delete(existing)
        session.commit()
        return {"liked": False}

    new_like = ReviewLike(user_id=current_user.id, review_id=review_id)
    session.add(new_like)
    session.commit()
    return {"liked": True}

# 하트 순 랭킹
def get_most_liked_reviews(session: Session):
    results = session.query(
        Review,
        func.count(ReviewLike.id).label('like_count')
    ).join(ReviewLike, isouter=True).group_by(Review.id).order_by(text('like_count DESC')).limit(10).all()

    trending_list = []
    for r, l_count in results:
        user = session.query(User).filter(User.id == r.user_id).first()
        rest = session.query(Restaurant).filter(Restaurant.id == r.restaurant_id).first()
        if user and rest:
            trending_list.append({
                "review_id": r.id,
                "nickname": user.nickname,
                "restaurant_name": rest.name,
                "content": r.content,
                "like_count": l_count,
                "image_url":r.image_url,
            })
    return trending_list


# 내 공개 설정 변경하기
@router.put("/privacy")
def update_privacy(request: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == current_user.id).first()
    user.is_public = request.get("is_public", True)
    session.commit()
    return {"message": "Success"}

# 특정 유저가 공개 상태인지 확인
@router.get("/{user_id}/status")
def get_user_status(user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    return {"is_public": user.is_public if user else True}

@router.post("/collections", status_code=201)
def create_collection_api(
        request: CreateCollectionRequest,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    create_collection(session,current_user.id, request)
    return {"msg": f"'{request.title}' 리스트가 성공적으로 발행되었습니다!"}

@router.get("/collections")
def get_collections_api(session: Session = Depends(get_db)):
    return get_all_collections(session)

@router.delete("/collections/{collection_id}", status_code=204)
def delete_collection_api(
        collection_id: int,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    success = delete_collection(session,collection_id,current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Collection not found")
    return

# 사용자가 댓글을 달고 DB에 저장되기까지의 5단계 흐름
# 1. 사용자가 웹사이트에서 리뷰 댓글 창에 댓글을 달고 게시 버튼을 누름
# 2. 프론트엔드의 포장 fetch() 함수를 쓸 때,body라는 곳에 넣음
# POST 방식으로 보냄, 서버의 주소로 보냄
# 3. body가 FastAPI 도착
# 4. 주소를 보니 댓글 등록 -> create_comment_api 호출
# content: str = Body(..., embed=True) URL에서 찾기 말고 Body를 열라함
# 5. content만 create_comment에게 넘겨줌 작업자는 DB에 저장 프론트에게 댓글 등록 완료 답변 보냄
@router.post("/reviews/{review_id}/comments", status_code=201)
def create_comment_api(
        review_id: int,
        content: str = Body(..., embed=True),
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    create_comment(session,current_user.id, review_id, content)
    return {"msg": "댓글이 등록되었습니다."}

@router.get("/reviews/{review_id}/comments", status_code=200)
def get_comments_api(review_id: int, session: Session = Depends(get_db)):
    return get_comments_by_review(session,review_id)

# [사용자 화면] "파스타 최고!" 입력
#       👇
# [프론트엔드]  body 상자에 담아 포장 📦 👉 { "content": "파스타 최고!" }
#       👇
#       🚀 (인터넷 통신 / POST 요청)
#       👇
# [백엔드 API]  Body(embed=True) 지시서 확인 📋 👉 상자 열고 "content" 알맹이만 꺼냄!
#       👇
# [DB 저장소]  "파스타 최고!" 문구 저장 완료 💾

# 주소가 함수로 연결되기까지의 5단계
# 1. 프론트엔드의 요청 발송
# 프론트엔드가 인터넷 선을 타고 백엔드 서버로 HTTP 요청을 보냄
# GET http://서버주소/users/5/followers
# app = FastAPI() main.py가 요청을 받음 주소 앞 부분인 /users/를 봄
# 회원 관리 Router로 넘김 / 남은 주소 /5/followers 확인
# @router.get("/{user_id}/followers"))확인하고 get_followers_api 호출
# get_followers_api 실행 repository.py의 get_user_followers DB에서 데이터 꺼냄
# 꺼낸 리스트를 JSON로 프론트엔드에 보냄 화면에 나타남
# router는 API주소들을 주제별로 묶어서 관리 해줌

@router.delete("/reviews/comments/{comment_id}", status_code=204)
def delete_comment_api(
        comment_id: int,
        session: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    success = delete_comment(session,comment_id,current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return

