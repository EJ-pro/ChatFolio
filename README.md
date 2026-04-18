# ChatFolio

## 프로젝트 실행 방법

```bash
# 가상환경 생성 및 활성화
uv venv .venv --python 3.13
.\.venv\Scripts\activate

# .env 파일 생성 
cp .env.sample .env

# docker-compose 실행
docker-compose -f docker-compose.yml up --build
```
