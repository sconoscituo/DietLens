# AI 사진 분석 라우터
import io
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.meal import Meal, MealItem
from app.services.gemini_vision import analyze_food_image
from app.services.nutrition import update_daily_log
from app.schemas.meal import AIAnalysisResult, MealResponse
from app.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from sqlalchemy.orm import selectinload
from PIL import Image, UnidentifiedImageError

router = APIRouter(prefix="/api/analysis", tags=["AI 분석"])


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@router.post("/upload", response_model=dict)
async def analyze_image(
    file: UploadFile = File(..., description="음식 사진"),
    meal_date: str = Form(..., description="식사 날짜 (YYYY-MM-DD)"),
    meal_type: str = Form(..., description="식사 종류 (아침/점심/저녁/간식)"),
    db: AsyncSession = Depends(get_db),
):
    """
    음식 사진을 업로드하고 Gemini Vision API로 분석합니다.
    분석 결과를 바탕으로 식사 기록을 생성합니다.
    """
    # 파일 검증
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 파일 크기 검증
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    # 실제 이미지 콘텐츠 검증 (Pillow)
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")

    # 저장 경로 설정
    upload_path = Path(UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = upload_path / filename

    # 파일 저장
    with open(file_path, "wb") as f:
        f.write(content)

    # AI 분석
    analysis = await analyze_food_image(str(file_path))

    # 식사 기록 생성
    from sqlalchemy import and_
    existing_result = await db.execute(
        select(Meal).options(selectinload(Meal.items)).where(
            and_(Meal.meal_date == meal_date, Meal.meal_type == meal_type)
        )
    )
    meal = existing_result.scalar_one_or_none()

    if not meal:
        meal = Meal(
            meal_date=meal_date,
            meal_type=meal_type,
            image_path=f"/uploads/{filename}",
            ai_analysis=analysis.get("analysis_text", ""),
        )
        db.add(meal)
        await db.flush()
    else:
        meal.image_path = f"/uploads/{filename}"
        meal.ai_analysis = analysis.get("analysis_text", "")

    # 분석된 음식 항목 추가
    for food_item in analysis.get("foods", []):
        item = MealItem(
            meal_id=meal.id,
            food_name=food_item.get("name", "알 수 없는 음식"),
            amount=float(food_item.get("amount", 100)),
            calories=float(food_item.get("calories", 0)),
            carbohydrates=float(food_item.get("carbohydrates", 0)),
            protein=float(food_item.get("protein", 0)),
            fat=float(food_item.get("fat", 0)),
        )
        db.add(item)

    await db.flush()

    # 합계 재계산
    await db.refresh(meal, ["items"])
    meal.total_calories = analysis.get("total_calories", sum(i.calories for i in meal.items))
    meal.total_carbohydrates = analysis.get("total_carbohydrates", sum(i.carbohydrates for i in meal.items))
    meal.total_protein = analysis.get("total_protein", sum(i.protein for i in meal.items))
    meal.total_fat = analysis.get("total_fat", sum(i.fat for i in meal.items))

    await db.flush()
    await update_daily_log(db, meal_date)
    await db.refresh(meal)

    return {
        "success": True,
        "meal_id": meal.id,
        "analysis": analysis,
        "image_url": f"/uploads/{filename}",
    }


@router.post("/analyze-only", response_model=AIAnalysisResult)
async def analyze_only(
    file: UploadFile = File(..., description="음식 사진"),
):
    """
    식사 기록 저장 없이 사진만 분석합니다.
    """
    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다.")

    # 실제 이미지 콘텐츠 검증 (Pillow)
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")

    upload_path = Path(UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    filename = f"tmp_{uuid.uuid4().hex}.{ext}"
    file_path = upload_path / filename

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        analysis = await analyze_food_image(str(file_path))
    finally:
        # 임시 파일 삭제
        if file_path.exists():
            file_path.unlink()

    return AIAnalysisResult(**analysis)
