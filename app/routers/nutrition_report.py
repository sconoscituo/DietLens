"""
주간 영양 리포트 라우터
"""
import json
from datetime import datetime, timedelta
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/nutrition-report", tags=["영양 리포트"])

try:
    from app.config import config
    GEMINI_KEY = config.GEMINI_API_KEY
except Exception:
    GEMINI_KEY = ""

try:
    from app.models.diet import DietLog
    HAS_DIET = True
except ImportError:
    HAS_DIET = False


@router.get("/weekly")
async def get_weekly_nutrition_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """주간 영양 섭취 리포트"""
    if not HAS_DIET:
        return {"message": "식단 모델이 없습니다"}

    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(DietLog).where(
            DietLog.user_id == current_user.id,
            DietLog.created_at >= week_ago
        )
    )
    logs = result.scalars().all()

    if not logs:
        return {"message": "이번 주 식단 기록이 없습니다", "logs_count": 0}

    # 영양소 합산
    total_calories = sum(getattr(l, "calories", 0) or 0 for l in logs)
    total_protein = sum(getattr(l, "protein", 0) or 0 for l in logs)
    total_carbs = sum(getattr(l, "carbohydrates", 0) or 0 for l in logs)
    total_fat = sum(getattr(l, "fat", 0) or 0 for l in logs)
    days = 7

    return {
        "period": "최근 7일",
        "logs_count": len(logs),
        "daily_average": {
            "calories": round(total_calories / days, 1),
            "protein_g": round(total_protein / days, 1),
            "carbs_g": round(total_carbs / days, 1),
            "fat_g": round(total_fat / days, 1),
        },
        "weekly_total": {
            "calories": total_calories,
            "protein_g": total_protein,
            "carbs_g": total_carbs,
            "fat_g": total_fat,
        },
        "recommended_daily": {
            "calories": 2000,
            "protein_g": 50,
            "carbs_g": 260,
            "fat_g": 65,
        }
    }


@router.get("/ai-advice")
async def get_nutrition_ai_advice(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 영양 섭취 조언"""
    if not HAS_DIET or not GEMINI_KEY:
        return {"advice": "AI 분석을 사용할 수 없습니다"}

    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(DietLog).where(
            DietLog.user_id == current_user.id,
            DietLog.created_at >= week_ago
        ).limit(20)
    )
    logs = result.scalars().all()
    if not logs:
        return {"advice": "식단 기록을 먼저 추가해주세요"}

    food_list = ", ".join([getattr(l, "food_name", "음식") for l in logs[:10]])
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"최근 7일 섭취 음식: {food_list}\n"
        "이 식단 패턴을 분석하고 영양 균형 개선을 위한 조언 3가지를 한국어로 알려줘."
    )
    return {"advice": response.text}
