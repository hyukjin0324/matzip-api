Key Features
맛집 데이터 수집: Naver Search API를 연동하여 실시간 음식점 정보를 수집 및 가공

위치 기반 시각화: Kakao Maps API를 활용한 지도 마커 렌더링 및 위치 데이터 처리

성능 최적화: Redis 인메모리 캐싱을 적용하여 반복되는 데이터 조회 속도 개선

배포 자동화: GitHub Actions를 통한 CI/CD 파이프라인 구축 (자동 테스트 및 배포)

컨테이너화: Docker & docker-compose를 사용하여 DB, Redis, App 환경 일치화

System Architecture
Backend: FastAPI (Asynchronous)

Storage: MySQL (Relational Data), Redis (Cache)

Deployment: AWS EC2, Docker-compose

CI/CD: GitHub Actions -> Docker Hub -> AWS EC2

Project Links
Live Demo: http://13.61.12.153:8000/

API Documents (Swagger): http://13.61.12.153:8000/docs
