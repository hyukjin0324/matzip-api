# 1. 어떤 컴퓨터 환경을 쓸 것인가? (파이썬 3.10이 설치된 가벼운 리눅스 버전 사용)
FROM python:3.10-slim

# 2. 도커 상자 안에서 우리가 작업할 폴더(디렉토리) 이름 지정
WORKDIR /app

# 3. 내 컴퓨터에 있는 requirements.txt를 도커 상자 안의 /app 폴더로 복사
COPY requirements.txt .

# 4. 도커 상자 안에서 필요한 라이브러리들 한 번에 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 내 컴퓨터에 있는 나머지 모든 코드(main.py 등)를 상자 안으로 복사
COPY . .

# 6. 도커 상자의 8000번 포트를 외부에 열어줌
EXPOSE 8000

# 7. 상자가 켜지면 마지막으로 실행할 서버 켜기 명령어 (uvicorn 실행)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]