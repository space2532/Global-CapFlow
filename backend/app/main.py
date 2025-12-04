from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import models
from .database import engine
from .routers import company

# Lifespan 방식으로 시작 시 DB 테이블 생성 (선택 사항, create_db.py가 있으므로 생략 가능하나 안전장치로 둠)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행될 로직
    # async with engine.begin() as conn:
    #     await conn.run_sync(models.SQLModel.metadata.create_all)
    yield
    # 종료 시 실행될 로직

app = FastAPI(
    title="Global CapFlow API",
    description="FastAPI + Async SQLAlchemy service",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 미들웨어 추가 (프론트엔드와의 통신을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.get("/health", summary="Application health check")
async def health() -> dict[str, str]:
    return {"status": "ok"}

# Router 등록
app.include_router(company.router)