# HTML 페이지 라우터
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.goal import Goal
from app.services.report import get_dashboard_data
from app.services.nutrition import get_daily_nutrition
from app.models.meal import Meal
from sqlalchemy.orm import selectinload

router = APIRouter(tags=["페이지"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    target_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """메인 대시보드 페이지"""
    if not target_date:
        target_date = date.today().isoformat()

    dashboard = await get_dashboard_data(db, target_date)

    # 최근 식사 기록 (오늘)
    meal_result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.items))
        .where(Meal.meal_date == target_date)
        .order_by(Meal.meal_type)
    )
    today_meals = meal_result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "dashboard": dashboard,
            "today_meals": today_meals,
            "target_date": target_date,
            "today": date.today().isoformat(),
        },
    )


@router.get("/log", response_class=HTMLResponse)
async def log_meal_page(
    request: Request,
    meal_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """식사 기록 페이지"""
    if not meal_date:
        meal_date = date.today().isoformat()

    daily = await get_daily_nutrition(db, meal_date)

    return templates.TemplateResponse(
        "log_meal.html",
        {
            "request": request,
            "meal_date": meal_date,
            "daily": daily,
            "today": date.today().isoformat(),
        },
    )


@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """AI 사진 분석 페이지"""
    today = date.today().isoformat()
    return templates.TemplateResponse(
        "analyze.html",
        {
            "request": request,
            "today": today,
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: AsyncSession = Depends(get_db)):
    """식사 기록 히스토리 페이지"""
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "today": date.today().isoformat(),
        },
    )


@router.get("/goals", response_class=HTMLResponse)
async def goals_page(request: Request, db: AsyncSession = Depends(get_db)):
    """목표 설정 페이지"""
    result = await db.execute(
        select(Goal).where(Goal.is_active == True).order_by(Goal.id.desc()).limit(1)
    )
    goal = result.scalar_one_or_none()

    return templates.TemplateResponse(
        "goals.html",
        {
            "request": request,
            "goal": goal,
            "today": date.today().isoformat(),
        },
    )


@router.get("/exercise", response_class=HTMLResponse)
async def exercise_page(request: Request):
    """운동 기록 페이지"""
    return templates.TemplateResponse(
        "exercise.html",
        {
            "request": request,
            "today": date.today().isoformat(),
        },
    )
