# 리포트 생성 서비스
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.daily_log import DailyLog
from app.models.goal import Goal
from app.services.nutrition import get_weekly_nutrition, calculate_nutrition_ratio
from datetime import date, timedelta


async def get_dashboard_data(db: AsyncSession, target_date: str) -> dict:
    """대시보드용 데이터를 수집합니다."""
    from app.services.nutrition import get_daily_nutrition

    # 오늘 데이터
    today_data = await get_daily_nutrition(db, target_date)

    # 현재 활성 목표
    goal_result = await db.execute(
        select(Goal).where(Goal.is_active == True).order_by(Goal.id.desc()).limit(1)
    )
    goal = goal_result.scalar_one_or_none()

    # 기본 목표값
    if not goal:
        goal_calories = 2000.0
        goal_carbs = 250.0
        goal_protein = 60.0
        goal_fat = 55.0
        goal_type = "유지"
    else:
        goal_calories = goal.daily_calories
        goal_carbs = goal.daily_carbohydrates
        goal_protein = goal.daily_protein
        goal_fat = goal.daily_fat
        goal_type = goal.goal_type

    # 진행률 계산
    today_cal = today_data["total_calories"]
    progress_pct = min(round(today_cal / goal_calories * 100, 1), 150) if goal_calories > 0 else 0

    # 주간 데이터
    weekly = await get_weekly_nutrition(db, target_date)

    # 영양소 비율
    ratio = calculate_nutrition_ratio(
        today_data["total_calories"],
        today_data["total_carbohydrates"],
        today_data["total_protein"],
        today_data["total_fat"],
    )

    # 남은 칼로리
    remaining_calories = max(0, goal_calories - today_cal)

    return {
        "today": {
            "date": target_date,
            "calories": today_cal,
            "carbohydrates": today_data["total_carbohydrates"],
            "protein": today_data["total_protein"],
            "fat": today_data["total_fat"],
            "meal_count": today_data["meal_count"],
            "meals_by_type": today_data["meals_by_type"],
        },
        "goal": {
            "type": goal_type,
            "calories": goal_calories,
            "carbohydrates": goal_carbs,
            "protein": goal_protein,
            "fat": goal_fat,
        },
        "progress": {
            "calories_pct": progress_pct,
            "remaining_calories": remaining_calories,
            "carbs_pct": min(round(today_data["total_carbohydrates"] / goal_carbs * 100, 1), 150) if goal_carbs > 0 else 0,
            "protein_pct": min(round(today_data["total_protein"] / goal_protein * 100, 1), 150) if goal_protein > 0 else 0,
            "fat_pct": min(round(today_data["total_fat"] / goal_fat * 100, 1), 150) if goal_fat > 0 else 0,
        },
        "nutrition_ratio": ratio,
        "weekly": weekly,
    }
