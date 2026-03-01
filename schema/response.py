from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# user 정보에는 비밀번호 같은 정보가 다 들어있음
# 방금 만든 데이터에서 UserSchema 양식에 맞는 것만 뽑아내라
class UserSchema(BaseModel):
    id: int
    username: str
    nickname: str

    # ORM 객체를 Pydantic 모델로 변환하기 위한 설정
    model_config = ConfigDict(from_attributes=True)

    # SQLAlchemy (DB) : 데이터를 .으로 꺼냄
    # user.id, user.username
    # pydantic (기본 설정) : 데이터를 [] (딕셔너리) 처럼 꺼냄
    # 설정을 안 하면 pydantic이 db를 받고 딕셔너리 아니라 못 읽음
    # 해결 (from_attributes=True)  pydantic -> .을 찍어 읽음

# 토큰 응답 (로그인 성공 시)
class TokenResponse(BaseModel):
    # 실제 데이터 암호화된 문자열로 되어 있음
    # 문자열 안에는 철수이고 30분 동안 유효하다 정보가 들어있음
    # 프론트엔드는 나중에 내 정보 보기 같은 요청을 할 때 문자열을 헤더에 붙여서 보냄
    access_token: str
    # 규칙 : Bearer -> 이 토큰을 가지고 있는 사람에게 권한을 줘라
    # 프론트엔드 개발자 헤더에 보낼 때 앞에 Bearer 라고 적어서 보내야 함
    token_type: str
    # 로그인한 사람의 아이디를 친절하게 알려줌
    # 프론트엔드 화면에 "000님 안녕하세요" 라고 띄워주기 위해
    username: str
    user_id: int

class RestaurantResponse(BaseModel):
    id: int
    name: str
    category: str
    address: str
    phone: Optional[str] = None
    img_url: Optional[str] = None
    created_at: datetime
    rating: float = 0.0
    review_count:int = 0
    class Config:
        from_attributes = True #orm 모드 활성화 (DB 데이터를 Pydantic으로 변환)

class ReviewResponse(BaseModel):
    id: int
    content: str
    rating: int
    view_count: int
    user_id: int
    nickname: Optional[str] = "익명"
    created_at: datetime
    restaurant_id: Optional[int] = None
    created_at: Optional[datetime] = None

    image_url: Optional[str] = None

    class Config:
        from_attributes = True



class RankingResponse(BaseModel):
    user_id : int
    title: str   # 리뷰 1등 , 조회수 1등
    nickname: str # 1등한 유저 닉네임
    score: int # 리뷰 갯수, 조회수
    message: str # 총 몇 개의 리뷰 작성, 조회수 달성



