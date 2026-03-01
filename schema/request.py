from pydantic import BaseModel
from typing import Optional, List


# 회원가입 요청
# BaseModel : Pydantic 이라는 라이브러리에서 제공하는 종이
# 자동으로 검사해줌

class CreateUserRequest(BaseModel):
    username: str
    password: str
    nickname: str

# 1. ORM : DB 테이블이랑 똑같이 생겨야함
# id 처럼 시스템이 자동으로 만드는 칸도 포함됨

# 2. Schema : class CreateUserRequest
# 손님이 입력해야 하는 것만 들어 있음
# 그래서 id는 양식에 빠져 있음

# 로그인 요청 (아이디, 비번만 입력)
class LoginRequest(BaseModel):
    username: str
    password: str

# 맛집 등록할 때 받는 데이터
class RestaurantCreate(BaseModel):
    name: str
    category: str
    address: str
    phone: Optional[str] = None # 없을 수도 있다
    img_url: Optional[str] = None

class CreateReviewRequest(BaseModel):
    restaurant_id: int
    content: str
    rating: int
    image_url: Optional[str] = None

class UpdateReviewRequest(BaseModel):
    content: str
    rating: int

#맛집 테마 리스트용 양식
class CreateCollectionRequest(BaseModel):
    title: str
    description: Optional[str] = None
    restaurant_ids: List[int] = []
