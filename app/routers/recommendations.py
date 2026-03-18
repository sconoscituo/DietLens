# AI 식단 추천 라우터
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.goal import Goal
from app.services.nutrition import get_daily_nutrition
from app.services.diet_recommender import get_next_meal_recommendation

router = APIRouter(prefix="/api/recommendations", tags=["AI 식단 추천"])


@router.get("/next-meal")
async def recommend_next_meal(
    target_date: Optional[str] = Query(None, description="날짜 (YYYY-MM-DD), 기본값: 오늘"),
    preferred_foods: Optional[str] = Query(None, description="선호 음식 키워드 (예: 닭고기, 채소)"),
    db: AsyncSession = Depends(get_db),
):
    """
    오늘 섭취 현황과 목표를 바탕으로 다음 식사를 AI가 추천합니다.
    """
    if not target_date:
        target_date = date.today().isoformat()

    # 오늘 섭취 현황 조회
    daily = await get_daily_nutrition(db, target_date)

    # 현재 활성 목표 조회
    result = await db.execute(
        select(Goal).where(Goal.is_active == True).order_by(Goal.id.desc()).limit(1)
    )
    goal = result.scalar_one_or_none()

    # 목표가 없으면 기본값 사용
    goal_calories = goal.daily_calories if goal else 2000.0
    goal_protein = goal.daily_protein if goal else 60.0
    goal_carbs = goal.daily_carbohydrates if goal else 250.0
    goal_fat = goal.daily_fat if goal else 55.0

    # 섭취 현황
    consumed_calories = daily.get("total_calories", 0.0)
    consumed_protein = daily.get("total_protein", 0.0)
    consumed_carbs = daily.get("total_carbohydrates", 0.0)
    consumed_fat = daily.get("total_fat", 0.0)

    recommendation = await get_next_meal_recommendation(
        goal_calories=goal_calories,
        consumed_calories=consumed_calories,
        goal_protein=goal_protein,
        consumed_protein=consumed_protein,
        goal_carbs=goal_carbs,
        consumed_carbs=consumed_carbs,
        goal_fat=goal_fat,
        consumed_fat=consumed_fat,
        preferred_foods=preferred_foods,
    )

    return {
        "target_date": target_date,
        "consumed": {
            "calories": consumed_calories,
            "protein": consumed_protein,
            "carbohydrates": consumed_carbs,
            "fat": consumed_fat,
        },
        "goal": {
            "calories": goal_calories,
            "protein": goal_protein,
            "carbohydrates": goal_carbs,
            "fat": goal_fat,
        },
        "recommendation": recommendation,
    }
