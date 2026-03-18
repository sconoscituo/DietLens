# 물 섭취 추적 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel, Field
from datetime import date
from app.database import get_db
from app.models.water import WaterLog

router = APIRouter(prefix="/api/water", tags=["물 섭취"])

# 일일 물 섭취 목표 (ml)
DAILY_WATER_GOAL_ML = 2000


class WaterLogCreate(BaseModel):
    user_date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    amount_ml: int = Field(..., ge=1, le=5000, description="섭취량 (ml)")


class WaterLogResponse(BaseModel):
    id: int
    user_date: str
    amount_ml: int

    class Config:
        from_attributes = True


class WaterSummary(BaseModel):
    user_date: str
    total_ml: int
    goal_ml: int
    percent: float
    logs: List[WaterLogResponse]


@router.post("/", response_model=WaterLogResponse, status_code=201)
async def add_water_log(data: WaterLogCreate, db: AsyncSession = Depends(get_db)):
    """물 섭취량을 기록합니다."""
    log = WaterLog(user_date=data.user_date, amount_ml=data.amount_ml)
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


@router.get("/summary/{target_date}", response_model=WaterSummary)
async def get_water_summary(target_date: str, db: AsyncSession = Depends(get_db)):
    """특정 날짜의 물 섭취 현황을 반환합니다."""
    result = await db.execute(
        select(WaterLog)
        .where(WaterLog.user_date == target_date)
        .order_by(WaterLog.logged_at)
    )
    logs = result.scalars().all()
    total_ml = sum(log.amount_ml for log in logs)
    percent = round(min(total_ml / DAILY_WATER_GOAL_ML * 100, 100), 1)
    return WaterSummary(
        user_date=target_date,
        total_ml=total_ml,
        goal_ml=DAILY_WATER_GOAL_ML,
        percent=percent,
        logs=logs,
    )


@router.delete("/{log_id}", status_code=204)
async def delete_water_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """물 섭취 기록을 삭제합니다."""
    result = await db.execute(select(WaterLog).where(WaterLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    await db.delete(log)
