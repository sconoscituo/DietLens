# 리포트 라우터
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date, timedelta
from app.database import get_db
from app.services.report import get_dashboard_data
from app.services.nutrition import get_daily_nutrition, get_weekly_nutrition

router = APIRouter(prefix="/api/reports", tags=["리포트"])


@router.get("/dashboard")
async def get_dashboard(
    target_date: Optional[str] = Query(None, description="날짜 (YYYY-MM-DD), 기본값: 오늘"),
    db: AsyncSession = Depends(get_db),
):
    """대시보드 데이터를 반환합니다."""
    if not target_date:
        target_date = date.today().isoformat()
    return await get_dashboard_data(db, target_date)


@router.get("/daily")
async def get_daily_report(
    target_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """일별 영양 리포트를 반환합니다."""
    if not target_date:
        target_date = date.today().isoformat()
    return await get_daily_nutrition(db, target_date)


@router.get("/weekly")
async def get_weekly_report(
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """주간 영양 리포트를 반환합니다."""
    if not end_date:
        end_date = date.today().isoformat()
    return await get_weekly_nutrition(db, end_date)


@router.get("/history")
async def get_history(
    days: int = Query(30, le=90, description="조회할 일수"),
    db: AsyncSession = Depends(get_db),
):
    """최근 N일간 기록을 반환합니다."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    from app.models.meal import Meal
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.items))
        .where(Meal.meal_date >= start.isoformat())
        .order_by(Meal.meal_date.desc(), Meal.meal_type)
    )
    meals = result.scalars().all()

    # 날짜별 그룹핑
    history = {}
    for meal in meals:
        if meal.meal_date not in history:
            history[meal.meal_date] = {
                "date": meal.meal_date,
                "total_calories": 0,
                "meals": [],
            }
        history[meal.meal_date]["total_calories"] += meal.total_calories
        history[meal.meal_date]["meals"].append({
            "id": meal.id,
            "meal_type": meal.meal_type,
            "calories": meal.total_calories,
            "items": [{"name": i.food_name, "calories": i.calories} for i in meal.items],
        })

    return list(history.values())
