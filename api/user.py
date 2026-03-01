from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from database.orm import User, Follow

from database.connection import get_db
from database.repository import create_user, get_user_by_username, get_user_by_nickname, get_user_followers, \
    get_user_following
from schema.request import CreateUserRequest, LoginRequest
from schema.response import UserSchema, TokenResponse
from security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM


# API 주소를 /users 로 시작하게 설정
router = APIRouter(prefix="/users")
# prefix 쓰면 기능들의 주소 앞에 /users를 붙이라고 선언 하는 것
# app = FastAPI() : 전체를 관리함
# router = APIRouter() : User 기능(회원가입, 로그인)을 담당함
# /users 로 묶으면 회원 관련 기능인 거 알 수 있음


# Swagger 자물쇠 버튼이 '/users/login'을 바라보게 함
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


# post : 데이터를 제출 할 때 쓰는 곳 (회원가입)
# 201번 -> 생성됨
@router.post("/signup", status_code=201)
def signup_handler(
        request: CreateUserRequest,
        session: Session = Depends(get_db)
        # request는 schema에서 가져옴 , db에서 session 가져옴
) -> UserSchema: #비밀 번호 숨겨야 함
    # 들어올 때는 필요해서 받았지만, 나갈 때는 버리고 나감

    # 1. 증복 아이디 검사
    if get_user_by_username(session, request.username):
        # raise : 에러를 강제로 발생시켜서, 코드를 멈추기
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    # 2. 비밀번호 암호화 해서 바꾸기
    # request 객체 안에 있는 password를 암호문으로 덮어씀
    request.password = get_password_hash(request.password)

    # 3. DB에 저장 (Repository 이용)
    user = create_user(session=session, request=request)

    # 4. 결과 반환 (Response Schema 이용)
    return UserSchema.model_validate(user)

# 로그인 (POST /users/login)
# LoginRequest schema에서 받아옴
# request: LoginRequest 로그인 할려면 신청서 양식에 맞춰서 제출
# db: DB 연결 통로 Session: DB 연결 객체
@router.post("/login", response_model=TokenResponse)
def login_handler(request: LoginRequest, db: Session = Depends(get_db)):
    # 아이디로 유저 찾기
    user = get_user_by_username(db, request.username)

    # 없거나 비밀번호 틀리면 에러
    # security.py에서 가져옴
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

    # 긴 문자열 만들기
    # security.py : 만드는 법을 적어 둠 (함수 정의)
    # user.py : 실제 재료를 넣어서 결과를 뽑아냄 (함수 호출)
    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token, # 진짜 토큰
        "token_type": "bearer", # 사용하는 방식
        "username": user.username, # user 정보
        "user_id": user.id
    }

# API 요청이 들어올 때마다 , Token이 진짜인지, 지금도 유효한지 검사
# JWT 토큰 : 비밀번호 없음
# get_current_user가 검사할 때 토큰에 있는 아이디로 DB를 뒤지기 때문에
# 비밀번호 정보를 찾게됨
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 토큰 해독 (암호 풀기)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # 토큰 안에 숨겨진 아이디 꺼내기
        if username is None:
            raise JWTError
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다.")
    # 만약 사용자가 로그인하고 5분 뒤에 관리자에 의해 강제 탈퇴당했다면?
    # 토큰 자체는 25분 남아서 통과함 , 마지막으로 DB에도 사람이 있는지 확인
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="유저를 찾을 수 없습니다.")
    return user

# 토큰을 통과 -> 내 정보 보기 (GET/users/me)
# get_me_handler 단순히 정보를 주는 역할만함
# 정보를 달라고 해도 누군지 모름
# get_current_user를 가져와 누군지 알아냄
@router.get("/me", response_model=UserSchema) #UserSchema에는 비밀번호x
# get_current_user로 토큰 검사하고 User를 찾아서 current_user에 저장해라
def get_me_handler(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/check-nickname")
def check_nickname_api(nickname:str, session: Session = Depends(get_db)):
    existing_user = get_user_by_nickname(session, nickname)
    if existing_user:
        return {"is_available": False}
    return {"is_available": True}


from sqlalchemy import text # 맨 위 import 모여있는 곳에 없다면 추가해주세요

# --- 기존 코드들 ---

# 🚀 DB 강제 수리 API (임시)
@router.get("/fix-db")
def fix_database(session: Session = Depends(get_db)):
    try:
        # user 테이블에 is_public 칸을 강제로 추가합니다.
        session.execute(text("ALTER TABLE user ADD COLUMN is_public BOOLEAN DEFAULT TRUE;"))
        session.commit()
        return {"msg": "✅ 성공! DB에 is_public 칸이 만들어졌습니다. 이제 원래 화면으로 돌아가세요!"}
    except Exception as e:
        return {"msg": f"💡 이미 만들어졌거나 다른 문제가 있습니다: {str(e)}"}


# ==========================================
# 🚀 1. 유저의 공개/비공개 상태 확인 API (이게 없어서 404 에러가 났습니다!)
# ==========================================
@router.get("/{user_id}/status")
def get_user_status(user_id: int, session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return {"is_public": user.is_public}


# ==========================================
# 🚀 2. 내 프로필 공개/비공개 설정 변경 API
# ==========================================
@router.put("/privacy")
def update_privacy(request: dict, current_user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    user = session.query(User).filter(User.id == current_user.id).first()

    # 프론트에서 보낸 'is_public' 값을 가져와서 내 상태 변경
    user.is_public = request.get("is_public", True)
    session.commit()
    return {"message": "공개 설정이 변경되었습니다."}


# ==========================================
# 🚀 3. 팔로우 / 언팔로우 토글 API
# ==========================================
@router.post("/follow/{target_user_id}")
def toggle_follow(
        target_user_id: int,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_db)
):
    if current_user.id == target_user_id:
        raise HTTPException(status_code=400, detail="자기 자신은 팔로우할 수 없습니다.")

    # 이미 팔로우 중인지 확인
    existing_follow = session.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == target_user_id
    ).first()

    if existing_follow:
        # 이미 팔로우 중이면 '언팔로우' 처리 (삭제)
        session.delete(existing_follow)
        session.commit()
        return {"followed": False}
    else:
        # 팔로우 중이 아니면 '팔로우' 처리 (추가)
        new_follow = Follow(follower_id=current_user.id, following_id=target_user_id)
        session.add(new_follow)
        session.commit()
        return {"followed": True}

@router.get("/{user_id}/followers")
def get_followers_api(user_id: int, session: Session = Depends(get_db)):
    return get_user_followers(session,user_id)

@router.get("/{user_id}/following")
def get_following_api(user_id: int, session: Session = Depends(get_db)):
    return get_user_following(session,user_id)