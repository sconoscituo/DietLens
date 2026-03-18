# 영양 정보 계산 서비스
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.meal import Meal, MealItem
from app.models.daily_log import DailyLog
from datetime import date, timedelta


async def get_daily_nutrition(db: AsyncSession, target_date: str) -> dict:
    """특정 날짜의 영양 집계를 계산합니다."""
    result = await db.execute(
        select(Meal).where(Meal.meal_date == target_date)
    )
    meals = result.scalars().all()

    total = {
        "date": target_date,
        "total_calories": 0.0,
        "total_carbohydrates": 0.0,
        "total_protein": 0.0,
        "total_fat": 0.0,
        "meal_count": len(meals),
        "meals_by_type": {
            "아침": None,
            "점심": None,
            "저녁": None,
            "간식": None,
        }
    }

    for meal in meals:
        total["total_calories"] += meal.total_calories
        total["total_carbohydrates"] += meal.total_carbohydrates
        total["total_protein"] += meal.total_protein
        total["total_fat"] += meal.total_fat
        total["meals_by_type"][meal.meal_type] = meal

    return total


async def get_weekly_nutrition(db: AsyncSession, end_date: str) -> List[dict]:
    """주간 영양 집계를 반환합니다."""
    end = date.fromisoformat(end_date)
    start = end - timedelta(days=6)

    weekly = []
    current = start
    while current <= end:
        date_str = current.isoformat()
        daily = await get_daily_nutrition(db, date_str)
        weekly.append({
            "date": date_str,
            "calories": daily["total_calories"],
            "carbohydrates": daily["total_carbohydrates"],
            "protein": daily["total_protein"],
            "fat": daily["total_fat"],
        })
        current += timedelta(days=1)

    return weekly


def calculate_nutrition_ratio(calories: float, carbs: float, protein: float, fat: float) -> dict:
    """영양소 비율 계산 (칼로리 기준)"""
    carb_cal = carbs * 4
    protein_cal = protein * 4
    fat_cal = fat * 9
    total = carb_cal + protein_cal + fat_cal

    if total == 0:
        return {"carbohydrates": 0, "protein": 0, "fat": 0}

    return {
        "carbohydrates": round(carb_cal / total * 100, 1),
        "protein": round(protein_cal / total * 100, 1),
        "fat": round(fat_cal / total * 100, 1),
    }


def scale_nutrition(food_data: dict, amount: float) -> dict:
    """섭취량에 따라 영양 정보를 비례 계산합니다."""
    serving = food_data.get("serving_size", 100.0)
    ratio = amount / serving if serving > 0 else 1.0

    return {
        "calories": round(food_data.get("calories", 0) * ratio, 1),
        "carbohydrates": round(food_data.get("carbohydrates", 0) * ratio, 1),
        "protein": round(food_data.get("protein", 0) * ratio, 1),
        "fat": round(food_data.get("fat", 0) * ratio, 1),
        "fiber": round(food_data.get("fiber", 0) * ratio, 1),
        "sodium": round(food_data.get("sodium", 0) * ratio, 1),
    }


async def update_daily_log(db: AsyncSession, target_date: str):
    """일별 집계 테이블을 갱신합니다."""
    daily = await get_daily_nutrition(db, target_date)

    result = await db.execute(
        select(DailyLog).where(DailyLog.log_date == target_date)
    )
    log = result.scalar_one_or_none()

    if log:
        log.total_calories = daily["total_calories"]
        log.total_carbohydrates = daily["total_carbohydrates"]
        log.total_protein = daily["total_protein"]
        log.total_fat = daily["total_fat"]
        log.meal_count = daily["meal_count"]
    else:
        log = DailyLog(
            log_date=target_date,
            total_calories=daily["total_calories"],
            total_carbohydrates=daily["total_carbohydrates"],
            total_protein=daily["total_protein"],
            total_fat=daily["total_fat"],
            meal_count=daily["meal_count"],
        )
        db.add(log)

    await db.flush()
