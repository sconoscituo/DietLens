# DietLens - AI 식단 트래커 메인 애플리케이션
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.config import APP_TITLE, APP_VERSION, UPLOAD_DIR
from app.database import init_db, AsyncSessionLocal
from app.models.food import Food
from app.routers import pages, foods, meals, analysis, goals, reports, water, exercise, weight, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 이벤트 핸들러"""
    # DB 초기화
    await init_db()

    # 업로드 디렉토리 생성
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # 한국 음식 초기 데이터 로드
    await seed_korean_foods()

    yield
    # 종료 시 처리 (필요시 추가)


async def seed_korean_foods():
    """한국 음식 영양 정보 DB를 초기 로드합니다."""
    data_path = Path("app/data/korean_foods.json")
    if not data_path.exists():
        return

    async with AsyncSessionLocal() as session:
        # 이미 데이터가 있으면 스킵
        result = await session.execute(select(Food).limit(1))
        if result.scalar_one_or_none():
            return

        with open(data_path, "r", encoding="utf-8") as f:
            foods_data = json.load(f)

        for food_data in foods_data:
            food = Food(**food_data)
            session.add(food)

        await session.commit()
        print(f"✅ 한국 음식 {len(foods_data)}개 초기 데이터 로드 완료")


# FastAPI 앱 생성
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="AI 기반 식단 관리 및 칼로리 트래커",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# 업로드 파일 제어 엔드포인트 (경로 탐색 방지 + 강제 이미지 Content-Type)
_SAFE_FILENAME_RE = re.compile(r'^[a-f0-9]{32,64}\.(jpg|jpeg|png|webp|gif)$')

@app.get("/uploads/{filename}")
async def serve_upload(filename: str):
    """업로드된 이미지를 안전하게 서빙합니다."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    file_path = Path(UPLOAD_DIR) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    suffix = file_path.suffix.lower()
    media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else f"image/{suffix.lstrip('.')}"
    return FileResponse(path=str(file_path), media_type=media_type)

# 라우터 등록 (API 라우터를 페이지보다 먼저 등록)
app.include_router(foods.router)
app.include_router(meals.router)
app.include_router(analysis.router)
app.include_router(goals.router)
app.include_router(reports.router)
app.include_router(water.router)
app.include_router(exercise.router)
app.include_router(weight.router)
app.include_router(recommendations.router)
app.include_router(pages.router)  # HTML 페이지는 마지막에


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
