# repository : API 라우터가 데이터가 필요할 때 Repository한테 요청하여
# ORM이라는 통역기를 들고 DB에 가서 데이터를 꺼내온 뒤, API에게 넘겨줌
# repository가 외부 데이터(Schema)를 내부 데이터(ORM)로 변환해주는 번역기임
# schema : 손님이 쓴 주문서(외부용)
# orm : 창고에 들어갈 규격
# repository : 주문서를 보고 박스에 물건을 옮겨 담는 작업자
from pydantic_core.core_schema import none_schema
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List

from schema.request import RestaurantCreate, CreateReviewRequest, CreateUserRequest, CreateCollectionRequest
from database.orm import User, Restaurant, Bookmark, Review, ReviewViewLog, Follow, Collection, CollectionItem, Comment


# ORM인 user를 import 함
# (session: Session) : Session 이 변수는 SQLAlchemy의 DB 세선 이어야 함
# request: 변수 이름
# :CreateUserRequest : Pydantic Schema 정해진 양식만 받음
# -> User : -> Return 결과물로 ORM 객체 하나를 뱉어낸다
def create_user(session: Session, request: CreateUserRequest) -> User:
    # ORM을 실제로 사용하는 건 repository
    new_user = User( # 왼쪽 new_user DB 테이블
                     # 오른쪽 Pydantic 데이터
        # username : DB에 있는 칸
        username=request.username,
        password=request.password,  # (주의) 지금은 암호화 안 함. 내일 구현 예정!
        nickname=request.nickname,
    )
    session.add(new_user)       # 메모리 RAM에는 올라감, DB에는 안 감
    session.commit()            # 저장 확정
    session.refresh(new_user)   # ID값 받아오기
    return new_user

# 아이디로 유저 찾기 (로그인용)
# db : 데이터베이스와 대화하는 직원(Session)
# SQLAlchemy의 Session이다 -> db. query,add,commit 자동 완성
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
# User 테이블 펼쳐서 테이블에 있는 username이랑 타이핑 한 name이랑 같은지 비교
# 아이디 중복은 안되니까 맨 위만 return

# 맛집 생성 함수 DB에 담기
def create_restaurant(session: Session, request: RestaurantCreate):

    existing = session.query(Restaurant).filter(Restaurant.name == request.name,
                Restaurant.address == request.address).first()

    if existing:
        return existing # 여기서 None 대신 existing을 반환하여 에러(500) 방지!

    new_restaurant = Restaurant(
        name = request.name,
        category = request.category,
        address=request.address,
        phone = request.phone,
        img_url = request.img_url,
    )
    session.add(new_restaurant)
    session.commit()
    session.refresh(new_restaurant)
    return new_restaurant

# 가게 명단 다 가져오기
# 가게 명단 다 가져오기
def get_all_restaurants(session: Session) -> List[dict]:
    restaurants = session.query(Restaurant).all()
    result = []
    for r in restaurants:
        revs = session.query(Review).filter(Review.restaurant_id == r.id).all()
        avg = sum([v.rating for v in revs]) / len(revs) if revs else 0.0
        result.append({
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "address": r.address,
            "phone": r.phone,
            "img_url": r.img_url,
            "rating": round(avg, 1),
            "review_count": len(revs),
            "created_at": r.created_at
        })
    return result
# session: 데이터베이스와 연결된 전화기, 창고지기
# session.query(Restaurant) : session이 Restaurant 테이블 좀 봐라
# .all() : 전부 가져와

# 찾아서 삭제하기
def delete_restaurant(session: Session, restaurant_id: int):
    # 1단계 : 지울거 찾기 (Search), restaurant_id인거 고르기
    target = session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    # 2단계 : 확인 및 삭제
    if target:
        session.delete(target) # 삭제 목록에 올려두기
        session.commit()
        return True
    return False

# 리뷰 저장
def create_review(session: Session, user_id: int, request: CreateReviewRequest):
    new_review = Review(
        user_id = user_id,
        restaurant_id = request.restaurant_id,
        content = request.content,
        rating = request.rating,
        view_count = 0,
        image_url = request.image_url
    )
    session.add(new_review)
    session.commit()
    session.refresh(new_review)
    return new_review

# 리뷰 목록 보기 (특정 가게의 리뷰들)
def get_reviews_by_restaurant_id(session: Session, restaurant_id: int):
    return session.query(Review).filter(Review.restaurant_id == restaurant_id).all()

# 리뷰 1개 자세히 보기 (볼 때마다 조회수 +1)
def get_review_detail(session: Session, review_id: int, user_id: int):
    review = session.query(Review).filter(Review.id == review_id).first()
    if review:
        already_viewed = session.query(ReviewViewLog).filter(
    ReviewViewLog.user_id == user_id,
            ReviewViewLog.review_id == review_id
        ).first()

        if not already_viewed:
          review.view_count+=1
          new_log = ReviewViewLog(user_id = user_id,review_id = review_id)
          session.add(new_log)
          session.commit()
          session.refresh(review)
    return review


# 평점은 ORM에서 계산했는가 -> 단일 객체의 가벼운 계산
# 이미 파이썬 메모리에서 리뷰 데이터가 다 올라와 있으니 파이썬의 SUM, LEN을 써서
# 가볍게 나누기만 하면 된다.

# 왜 랭킹은 Repository(DB)에서 계산했나 -> 전체 테이블 대상의 무거운 통계
# 이걸 ORM에서 계산한다면 DB 메모리를 다 가져와야 함 -> 메모리 폭발
# MYSQL은 Group By, Count, Order By에 특화됨

def get_review_king(session: Session):
    # DB에는 3명의 유저 6개의 리뷰가 있다. 철수, 영희, 민수 , 리뷰 A~F
    #.join 작성자 번호(user_id)를 기준으로 하나로 합친다.
    # 철수 A,B,C 영희 D , 민수 E,F
    #.group_by(User.id) 같은 유저끼리 묶으라고 명령함
    # func.count(Review.id) 리뷰 갯수 세기
    #.order_by 내림차순 줄 세우기
    # func.count(Review.id): 리뷰 갯수 세기
    # group_by (User.id): 유저별로 묶기
    # order_by(desc()): 내림차순 정렬
    # first() : 그 중 1등만 가져오기
    result = session.query(
        User,
        func.count(Review.id).label('review_count')
        # DB에 Query를 할 것이다.
        # User, 테이블에 있는 유저 1명의 모든 정보를 주세요
        # 리뷰 테이블의 고유번호가 몇 개 있는지 COUNT 함
        # func : SQLAlchemy가 제공하는 func를 사용해서 DB 엔진이 직접 계산
    ).join(Review, User.id == Review.user_id).group_by(User.id).order_by(func.count(Review.id).desc()).first()
    return result
    # 합치기 전 DB에는 테이블이 따로 떨어져 있음
    # User , Review .join User 파일 옆에 Review 파일도 가져와서 붙여라
    # 회원의 id 번호랑 리뷰의 user_id 번호가 똑같은 것끼리 짝을 맞춰서 붙여라
    # join을 쓰지 안흥면 몇 개 썼는지 알 수 없음

# 리뷰 총 조회수가 가장 높은 사람
def get_popular_star(session: Session):
    #func.sum(Review.view_count): 조회수 다 더하기
    result = session.query(
        User,
        func.sum(Review.view_count).label('total_views')
    ).join(Review, User.id == Review.user_id).group_by(User.id).order_by(func.sum(Review.view_count).desc()).first()
    return result

# 찜하기
def create_bookmark(session:Session, user_id:int, restaurant_id: int)->Bookmark:
    # 중복 확인
    exists = session.query(Bookmark).filter_by(user_id = user_id,restaurant_id = restaurant_id).first()
    if exists:
        return exists

    # 새 bookmark 작성
    new_bookmark = Bookmark(user_id = user_id,restaurant_id = restaurant_id)
    session.add(new_bookmark)
    session.commit()
    session.refresh(new_bookmark)
    return new_bookmark

# 찜 취소
def delete_bookmark(session: Session, user_id: int, restaurant_id: int):
    # 지울 포스트잇 찾기
    bookmark = session.query(Bookmark).filter_by(user_id = user_id,restaurant_id = restaurant_id).first()
    if bookmark:
        session.delete(bookmark)
        session.commit()

# 나만의 목록 가져오기
def get_user_bookmark(session: Session, user_id: int):
    # 상단에 바로 return이 있으면 안 됩니다! 데이터를 먼저 정의해야 합니다.
    bookmarks = session.query(Restaurant).join(Bookmark, Restaurant.id == Bookmark.restaurant_id).filter(Bookmark.user_id == user_id).all()
    result = []
    for r in bookmarks:
        # 이 식당에 달린 모든 리뷰 점수 가져오기
        revs = session.query(Review).filter(Review.restaurant_id == r.id).all()
        avg = sum([v.rating for v in revs]) / len(revs) if revs else 0.0
        result.append({
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "address": r.address,
            "img_url": r.img_url,      # 네이버에서 가져온 진짜 사진 주소
            "rating": round(avg, 1),   # 진짜 별점 평균
            "review_count": len(revs),  # 진짜 리뷰 개수
            "created_at": r.created_at
        })
    return result

# DB를 뒤져서 입력받은 이름과 똑같은 식당이 있는지 하나만 찾아옴
def get_restaurant_by_name(session: Session, name: str) -> Restaurant:
    return session.query(Restaurant).filter(Restaurant.name == name).first()

# 리뷰 수정하기
def update_review(session: Session, review_id: int, user_id:int, content:str,rating:int):
    # 수정할 리뷰 찾기
    review = session.query(Review).filter(Review.id == review_id, Review.user_id == user_id).first()

    if review:
        review.content = content
        review.rating = rating
        session.commit()
        session.refresh(review)
        return review
    return None
# 리뷰 삭제하기
def delete_review(session: Session, review_id: int, user_id: int):
    review = session.query(Review).filter(Review.id == review_id, Review.user_id == user_id).first()
    if review:
        session.delete(review)
        session.commit()
        return True
    return False

# 특정 유저가 작성한 리뷰 다 가져오기
def get_user_reviews(session: Session, user_id: int):
    return session.query(Review).filter(Review.user_id == user_id).order_by(Review.created_at.desc()).all()

# 닉네임으로 유저 찾기( 닉네임 중복 검사용)
def get_user_by_nickname(session: Session, nickname: str):
    return session.query(User).filter(User.nickname == nickname).first()


# 유저의 프로필 공개/비공개 상태를 확인합니다.
def get_user_status_repo(session: Session, user_id: int):
    user = session.query(User).filter(User.id == user_id).first()
    # 유저가 없거나, is_public 값이 없으면 기본적으로 True(공개)로 처리합니다.
    return user.is_public if user else True

# 유저의 프로필 공개/비공개 설정을 변경합니다.
def update_user_privacy_repo(session: Session, user_id: int, is_public: bool):
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.is_public = is_public
        session.commit()

# 특정 유저를 팔로우하거나, 이미 팔로우 중이면 언팔로우(취소) 합니다.
def toggle_user_follow_repo(session: Session, current_user_id: int, target_user_id: int):
    # 1. DB 창고(Follow 테이블)에서 내가 저 사람을 이미 팔로우했는지 기록을 찾습니다.
    existing = session.query(Follow).filter(
        Follow.follower_id == current_user_id,
        Follow.following_id == target_user_id
    ).first()

    if existing:
        # 2-A. 기록이 있다면? -> 한 번 더 누른 거니까 팔로우 취소(삭제) 처리!
        session.delete(existing)
        session.commit()
        return False # "이제 팔로우 안 함" 이라는 뜻으로 False 반환
    else:
        # 2-B. 기록이 없다면? -> 새로 팔로우(추가) 처리!
        new_follow = Follow(follower_id=current_user_id, following_id=target_user_id)
        session.add(new_follow)
        session.commit()
        return True # "이제 팔로우 함" 이라는 뜻으로 True 반환


# 컬렉션 생성
# 새로운 맛집 리스트를 만드는 작업
# 창고 문 열기 : session, 누가 만든 건지 이름 달기 : user_id
# 리스트 제목이랑 어떤 식당들 담을 건지 알아야 함 : request
# 새로 만들기(POST), 수정 할 때는 request 필요
def create_collection(session: Session, user_id: int, request: CreateCollectionRequest):
    new_collection = Collection(
        user_id = user_id,
        title = request.title,
        description = request.description
    )
    session.add(new_collection)
    session.commit()
    session.refresh(new_collection)

    for rest_id in request.restaurant_ids:
        new_item = CollectionItem(collection_id=new_collection.id, restaurant_id=rest_id)
        session.add(new_item)
    session.commit()
    return new_collection


# 식당들 담기
# 이미 만들어진 맛집 리스트를 보여주는 역할
# 단순히 데이터 조회(GET)만 할 때 session만 적음
def get_all_collections(session: Session):
    collections = session.query(Collection).order_by(Collection.id.desc()).all()
    result = []

    # 상자를 하나씩 열어서 내용물 확인하기
    for collection in collections:
        # 유저 찾기
        user = session.query(User).filter(User.id == collection.user_id).first()
        # 식당 찾기
        items = session.query(CollectionItem).filter(CollectionItem.collection_id == collection.id).all()

        rest_list = []
        for item in items:
            rest = session.query(Restaurant).filter(Restaurant.id == item.restaurant_id).first()
            if rest:
                rest_list.append({
                    "id" : rest.id,
                    "name": rest.name,
                    "category": rest.category,
                    "address": rest.address
                })

        result.append({
            "collection_id": collection.id,
            "user_id" : collection.user_id,
            "nickname": user.nickname if user else "익명",
            "title": collection.title,
            "description": collection.description,
            "restaurants": rest_list
        })
    return result

# 처음부터 식당 정보를 다 담지 않고 고유 번호만 담는 이유
# 예를 들어 천 명의 유저가 이재모 피자를 저장했다고 가정하면
# DB에 번호가 아니라 글자 그대로 이재모 피자를 저장했다면
# 이재모 피자 -> 부산 이재모 피자 본점으로 바뀜
# 천 명의 유저 리스트를 일일이 다 뒤져서 수정해야함
# 번호만 저장했을 때 Restaurant 테이블에 가서 딱 1번만 이름 바꿈
# 관계형 데이터베이스

# 컬렉션 삭제
def delete_collection(session: Session, collection_id: int, user_id: int):
    collection = session.query(Collection).filter(Collection.id == collection_id).first()

    # ❌ 컬렉션이 없거나, 주인이 아니면 False 반환
    if not collection or collection.user_id != user_id:
        return False

    session.query(CollectionItem).filter(CollectionItem.collection_id == collection.id).delete()
    session.delete(collection)
    session.commit()
    return True

# 댓글 저장
def create_comment(session:Session, user_id:int, review_id:int, content:str):
    new_comment = Comment(user_id=user_id, review_id=review_id, content=content)
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    return new_comment

# 특정 리뷰의 댓글 목록 가져오기
def get_comments_by_review(session: Session, review_id: int):
    # 작성자 닉네임까지 한꺼번에 가져옴
    comments = session.query(Comment).filter(Comment.review_id == review_id).order_by(Comment.id.asc()).all()

    result = []
    for comment in comments:
        user = session.query(User).filter(User.id == comment.user_id).first()
        result.append({
            "id": comment.id,
            "review_id": comment.review_id,
            "user_id" : comment.user_id, # 프론트에서 내 댓글인지 확인하기 위해 필수
            "nickname": user.nickname if user else "익명",
            "content": comment.content,
            "created_at": comment.created_at
        })
    return result

# 댓글 삭제 기능
def delete_comment(session: Session, comment_id: int, user_id: int):
    comment = session.query(Comment).filter(Comment.id == comment_id, Comment.user_id == user_id).first()
    if comment:
        session.delete(comment)
        session.commit()
        return True
    return False

# 팔로워 목록
def get_user_followers(session: Session, user_id: int):
    follows = session.query(Follow).filter(Follow.following_id == user_id).all()
    result = []
    for f in follows:
        u = session.query(User).filter(User.id == f.follower_id).first()
        if u:
            result.append({"user_id": u.id, "nickname": u.nickname})
    return result

# 팔로잉 목록
def get_user_following(session: Session, user_id: int):
    follows = session.query(Follow).filter(Follow.follower_id == user_id).all()
    result = []
    for f in follows:
        u = session.query(User).filter(User.id == f.following_id).first()
        if u:
            result.append({"user_id": u.id, "nickname": u.nickname})
    return result

def toggle_user_follow_repo(session: Session, current_user_id: int, target_user_id: int):
    existing = session.query(Follow).filter(
        Follow.follower_id == current_user_id,
        Follow.following_id == target_user_id
    ).first()

    if existing:
        session.delete(existing)
        session.commit()
        return False
    else:
        new_follow = Follow(follower_id=current_user_id, following_id=target_user_id)
        session.add(new_follow)
        session.commit()
        return True

