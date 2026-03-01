from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# create_all이 실행되면 파이썬이 이 주소로 찾아가서 MySQL 프로그램 안에 있는
# oz_fastapi 구역에 user 테이블을 만든다

DATABASE_URL = "mysql+pymysql://root:todos@127.0.0.1:3306/oz_fastapi"

engine = create_engine(DATABASE_URL, echo=True)
# 파이썬이 MYSQL이랑 연결됨, True로 해두면 파이선 코드가 실행될 때 실제로 어떤 SQL 문장이 날아가는지 터미널에 다 보여줌
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Engine이 은행 건물이면 Session은 은행원이다.
# Engine = MYSQL와 실제로 연결되는 물리적 통로
# DB에 데이터를 넣거나 뺄 때 Session을 찍어내는 공장을 만듬
# autocommit = False 자동 저장 끄기
# autoflush = False 임시 저장 끄기
# bind = engine SessionFactory는 engine이랑 연결됨
# Session = Query를 하면 , Engine에 가서 가져옴
# session.add() , session.scalar() 하면 DB에 가서 일 처리함

def get_db():
    session = SessionFactory() # DB 연결 생성
    try:
        yield session # 중단 main.py로 넘어감 , yield 값을 던져주고 함수 상태 유지 및 대기
    finally:
        session.close() # 연결 종료
# 연결 관리 작업