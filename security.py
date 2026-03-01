
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

# bcrypt라는 강력한 알고리즘 사용
# deprecated = "auto": 예전 방식이 있으면 자동으로 최신 방식으로 업데이트하라는 뜻

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# bcrypt : 비밀번호 전용 해시 알고리즘
# 암호문을 알아도 비밀번호를 알아낼 수 없다
# 똑같은 비밀번호를 넣어도 매번 결과가 다르게 나옴

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# [기능 1] 비밀번호 갈아버리기 (회원가입용)
# - 입력: "1234"
# - 출력: "$2b$12$EixZa"
# - 특징: 한 번 암호화되면 절대 원래대로 되돌릴 수 없음 (복호화 불가능)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# [기능 2] 비밀번호 맞는지 확인하기 (로그인용)
# - 입력 1: 1234
# - 입력 2: "$2b$12$" (DB에 저장되어 있던 암호화된 비밀번호)
# - 동작: 입력 1을 똑같이 암호화해서 입력 2와 모양이 같은지 비교
# - 결과: 같으면 true, 다르면 false

# return pwd_context.hash("1234")
# bcrypt 암호화 전 무작위 문자열 생성
# Hashing: 비밀번호 + 무작위 합쳐서 돌림

# verify_password
# bcrypt DB에 저장된 암호를 보고 무작위 부분 뽑아냄
# Re-hashing: 방금 입력한 비밀번호 + 무작위 부분
# 똑같으면 true 다르면 false

# 해싱 vs 암호화
# 해싱 : 암호화만, 내용 같은지 비교, 비밀번호 저장
# 암호화 : 암호화 <-> 복호화, 내용 확인, 편지 파일 전송

# 비밀번호 암호화 (Bcrypt)
# 보관용 , 회원가입할 때, 로그인 순간, 복호화 불가능
# 서버는 비밀번호 원본을 알 필요 x, 암호화 덩어리 비교만 하면됨

# JWT 토큰 (Access Token)
# 전송용(로그인 상태 유지), 로그인 성공 후 모든 API 요청마다, 복호화 가능
# 철수가 프로필을 보여달라고 하면? DB에서 꺼내야함
# API 요청이 들어올 때마다 서버는 누가 요청하는지 알아야함
# JWT 안의 내용: sub(식별), exp(유효기간), role(권한)
# JWT 읽기 가능, 수정 불가능


# 로그인이 성공하면 출입증(토큰)을 만들어주는 기계가 필요
SECRET_KEY = "oz_fastapi_secret_key" # 비밀 도장, 서버만 알고 있음
ALGORITHM = "HS256" # 도장 찍는 기술
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 30동안 유효

def create_access_token(data: dict):
    # 유저 아이디가 있는 data를 바아 encoded_jwt를 만듬
    to_encode = data.copy()
    # 지금이 5시라면 5시 30분까지
    expire = (datetime.now(timezone.utc) +
              timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


    to_encode.update({"exp": expire})
    # 내용물 , SECRET_KEY : 내용 뒤섞음, ALGORITHM 방식
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt
