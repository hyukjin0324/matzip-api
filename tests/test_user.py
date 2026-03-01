# src/tests/test_user.py
# 회원가입이 잘 되는지 점검
# client : 로봇 /users/signup 에 가서 post 함
def test_signup(client):
    # 1. 회원가입 요청 보내기 (이름, 비번, 닉네임)
    response = client.post(
        "/users/signup", # 주소
        json={ # 보낼 데이터
            "username": "tester1",
            "password": "password123",
            "nickname": "맛집탐험가"
        }
    )

    # assert: 이거 아니면 당장 에러 내고 멈추라는 명령어
    # 2. 결과 검사: 상태 코드가 201(생성됨)이어야 성공!
    assert response.status_code == 201

    # 3. 결과 검사: 반환된 데이터에 비번은 없어야 하고, 닉네임은 맞아야 함
    data = response.json()
    assert data["username"] == "tester1"
    assert data["nickname"] == "맛집탐험가"
    assert "password" not in data  # 비밀번호는 보안상 돌려주면 안 됨!

    # JSON : 컴퓨터끼리 대화할 때 쓰는 공통 언어
    # 서버 : python, browser : JS , Iphone: swift -> JSON이라는 포장지 사용