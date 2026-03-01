from sqlalchemy import Column, Integer, String, create_engine, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


# 파이썬은 객체언어를 쓰고, 데이터베이스는 SQL이라는 언어를 씀
# ORM은 파이썬 코드만 써도 SQL로 번역되어 DB에 날아감
# 파이썬이 이해할 수 있는 방식으로 번역해 둔 DB 테이블의 설계도
Base = declarative_base()
# Base : 아무것도 그려지지 않은 빈 모눈종이

# 회원 (User) 테이블
# User 라는 설계도를 그림
# 실제 MySQL에 들어갈 테이블의 이름
class User(Base):
    __tablename__ = 'user'
    # id : 데이터 고유번호
    # Integer : 숫자만 들어감
    # primary_key = True : 겹치면 안되는 번호
    # index = True : 즐겨찾기(색인) 설정
    # 나중에 100번 회원 찾아줘 하면 목차를 보고 찾게 해줌
    id = Column(Integer, primary_key=True, index=True)
    # 아이디 최대 50글자
    # unique = True : 중복 금지
    # nullable = False : 빈칸 금지
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    nickname = Column(String(50), nullable=False)
    # 내가 쓴 리뷰 리스트
    reviews = relationship("Review", back_populates="user")
    # 유저가 자신의 찜 목록 볼 수 있음
    bookmarks = relationship("Bookmark", back_populates="user")

    # 프로필 및 찜 목록 공개 여부 (True: 공개, False : 비공개)
    is_public = Column(Boolean, default=True)

    #내가 팔로우하는 사람들
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    followers = relationship("Follow", foreign_keys="Follow.following_id",back_populates="following_user")



    # 기능에는 영향 x
    # 나중에 에러가 났을 때 컴퓨터가 <User obejct at 0x1234> 대신
    # User(id=1, username=hyukjin) 처럼 보여줌
    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, nickname={self.nickname})"



# 맛집 테이블
class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    category = Column(String(50), nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True) # 번호 없는 곳도 있음
    img_url = Column(String(500), nullable=True)
    # 등록 시간
    created_at = Column(DateTime, default=func.now())

    # 이 가게에 달린 리뷰 리스트
    reviews = relationship("Review", back_populates="restaurant")
    bookmarks = relationship("Bookmark", back_populates="restaurant")

    # 평균 평점 계산기
    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0

        # 리뷰들의 rating을 다 더해서 갯수로 나눔
        total_score = sum(r.rating for r in self.reviews)
        return round(total_score / len(self.reviews), 1)

# 리뷰 테이블
class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(500), nullable=False)
    rating = Column(Integer, nullable=False)

    view_count = Column(Integer, default=0)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # 누구랑 연결되는지
    user_id = Column(Integer, ForeignKey('user.id'))
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))

    # relationship 파이썬 코드에서 review.user 라고 치면 숫자를 가지고
    # User 테이블에 가서 유저의 모든 정보를 객체로 가져와
    # back_populates : 자동 업데이트
    user = relationship("User", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")
    comments = relationship("Comment", back_populates="review")

# DB 테이블: 변하지 않는 사실만 저장
# 평균 점수 : 계산 결과이므로 굳이 저장해서 용량을 차지하거나 동기화 걱정 할 필요 x
# orm: 여기에 넣어두면 , Repository가 데이터를 가져올 때 자동으로 계산해서 API에게 넘겨줌


# Bookmark 테이블
# User : 철수
# Restaurant : 영등포 꽃삼
# Bookmark: 철수가 영등포꽃삼을 찜했다

class Bookmark(Base):
    __tablename__ = 'bookmarks'
    id = Column(Integer, primary_key=True, index=True)
    # 누가 찜했나
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    # 어떤 식당을 찜했는가
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    # 언제 찜했는가
    created_at = Column(DateTime, default=func.now())
    # 관계 설정
    user = relationship("User", back_populates="bookmarks")
    restaurant = relationship("Restaurant", back_populates="bookmarks")


# 조회 기록 DB를 만드는 이유
# 기존에는 view_count 만 있었음 누가 리뷰를 클릭하던간에 조회수가 상승함
# DB를 만들면 이름 DB를 만듬 user_id, review_id
# [혁진, 1번 리뷰]라고 적어두고, 조회수 +1
# 다시 클릭하면 조회수 올리지 않고 리뷰 내용만 보여줌

class ReviewViewLog(Base):
    __tablename__ = 'review_view_log'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    review_id = Column(Integer, ForeignKey('reviews.id'))

# 리뷰 좋아요 테이블
class ReviewLike(Base):
    __tablename__ = 'review_like'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    review_id = Column(Integer, ForeignKey('reviews.id'))

# 팔로우 테이블
class Follow(Base):
    __tablename__ = 'follow'
    __table_args__ = (UniqueConstraint('follower_id', 'following_id', name='uq_follow_pair'),)
    id = Column(Integer, primary_key=True, index=True)
    # 팔로우를 누른 사람
    follower_id = Column(Integer, ForeignKey('user.id'))
    # 팔로우를 당한사람
    following_id = Column(Integer, ForeignKey('user.id'))

    follower = relationship("User", foreign_keys=[follower_id],back_populates="following")
    following_user = relationship("User", foreign_keys=[following_id],back_populates="followers")

# 맛집 리스트 테이블 컬렉션 제목과 설명(강남 맛집 리스트)
class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(100), nullable=False) #리스트 제목
    description = Column(String(500), nullable=False) #리스트 설명
    created_at = Column(DateTime, default=func.now())
    user = relationship("User")
    items = relationship("CollectionItem", back_populates="collection")

# 컬렉션 안에 담길 식당들의 목록
class CollectionItem(Base):
    __tablename__ = 'collection_items'
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey('collections.id'))
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))

    collection = relationship("Collection", back_populates="items")
    restaurant = relationship("Restaurant")

# 댓글 데이터 저장
class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    review_id = Column(Integer, ForeignKey('reviews.id'))
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())

    #관계 설정
    user = relationship("User")
    review = relationship("Review", back_populates="comments")
