


import pytest

from starlette.testclient import TestClient

# [수정 전] from main import router
# [수정 후] main.py에 있는 'app'을 가져와야 합니다.
from main import app

@pytest.fixture
def client():
    # TestClient에 router 대신 app을 넣어줍니다.
    return TestClient(app=app)

# TestClient: 가상의 웹 브라우저
# 크롬처럼 서버에 로그인, 가입 요청을 보낼 수 있는 로봇
# @pytest.fixture : 다른 테스트 파일들이 client 부르면 로봇을 빌려줌