import redis
import json
import os
from sqlalchemy import text
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.responses import FileResponse

from api import user, restaurant
from database.connection import engine  # 추가된 부분 1
from database.orm import Base           # 추가된 부분 2
from fastapi.middleware.cors import CORSMiddleware # 프론트엔드
from database.orm import ReviewViewLog
from database.connection import engine



app = FastAPI()
# Redis 연결 (로컬호스트의 6379 포트)
rd = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
# orm.py 작성 설계도 완성, DB 상태 테이블 없음
# main.py 실행 (create_all) DB User 테이블 생성됨
# [핵심] 서버가 켜질 때, DB에 테이블이 없으면 자동으로 만들어라!

# 서버에 사진을 저장할 폴더를 자동으로 만듬
os.makedirs("static/uploads", exist_ok=True)

# 브라우저에서 /static/ ... 주소로 사진을 볼 수 있게함
app.mount("/static", StaticFiles(directory="static"), name="static")

# 👇 이 설정이 있어야 프론트엔드에서 요청을 보낼 수 있습니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 곳에서 오는 요청 허용 (보안상 실제 배포땐 특정 주소만 넣음)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT... 다 허용
    allow_headers=["*"],
)

# engine은 파이썬과 MYSQL을 연결해줌
with engine.connect() as conn:
    try:
        # reviews 테이블에 image_url 칸을 새로 만들어라! 라는 직접 명령입니다.
        conn.execute(text("ALTER TABLE reviews ADD COLUMN image_url VARCHAR(255) DEFAULT NULL;"))
        conn.commit()
        print("✅ reviews 테이블에 image_url 컬럼이 성공적으로 추가되었습니다!")
    except Exception as e:
        # 이미 컬럼이 만들어졌거나 에러가 나면 그냥 넘어갑니다.
        print("💡 이미 컬럼이 존재하거나 추가 중 오류 발생 (무시해도 됨):", e)
# 딱 한 번만 실행할 임시 코드
# ReviewViewLog.__table__.drop(engine, checkfirst=True)
with engine.connect() as conn:
    try:
        # 1. 유저 테이블에 공개여부 칸 추가
        conn.execute(text("ALTER TABLE user ADD COLUMN is_public BOOLEAN DEFAULT TRUE;"))
        conn.commit()
    except: pass # 이미 있으면 무시
Base.metadata.create_all(bind=engine)

# User를 메인에 넣음
app.include_router(user.router)
app.include_router(restaurant.router)

@app.get("/")
def read_root():
    # 현재 파일 위치를 기준으로 절대 경로를 찾아서 index.html을 보여줍니다.
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_path, "static", "index.html")
    return FileResponse(file_path)

