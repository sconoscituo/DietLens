# 체중 기록 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.weight import WeightLog

router = APIRouter(prefix="/api/weight", tags=["체중 기록"])


class WeightLogCreate(BaseModel):
    log_date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    weight_kg: float = Field(..., ge=20, le=300, description="체중 (kg)")
    body_fat_pct: Optional[float] = Field(None, ge=1, le=80, description="체지방률 (%)")


class WeightLogResponse(BaseModel):
    id: int
    log_date: str
    weight_kg: float
    body_fat_pct: Optional[float]

    class Config:
        from_attributes = True


@router.post("/", response_model=WeightLogResponse, status_code=201)
async def create_weight_log(data: WeightLogCreate, db: AsyncSession = Depends(get_db)):
    """체중을 기록합니다. 같은 날짜가 있으면 덮어씁니다."""
    # 같은 날짜 기록이 있으면 업데이트
    result = await db.execute(select(WeightLog).where(WeightLog.log_date == data.log_date))
    existing = result.scalar_one_or_none()
    if existing:
        existing.weight_kg = data.weight_kg
        existing.body_fat_pct = data.body_fat_pct
        await db.flush()
        await db.refresh(existing)
        return existing

    log = WeightLog(
        log_date=data.log_date,
        weight_kg=data.weight_kg,
        body_fat_pct=data.body_fat_pct,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


@router.get("/", response_model=List[WeightLogResponse])
async def list_weight_logs(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """최근 체중 기록 목록을 반환합니다."""
    result = await db.execute(
        select(WeightLog)
        .order_by(WeightLog.log_date.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    # 날짜 오름차순으로 반환 (차트용)
    return list(reversed(logs))


@router.get("/{log_id}", response_model=WeightLogResponse)
async def get_weight_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """특정 체중 기록을 반환합니다."""
    result = await db.execute(select(WeightLog).where(WeightLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="체중 기록을 찾을 수 없습니다.")
    return log


@router.put("/{log_id}", response_model=WeightLogResponse)
async def update_weight_log(
    log_id: int, data: WeightLogCreate, db: AsyncSession = Depends(get_db)
):
    """체중 기록을 수정합니다."""
    result = await db.execute(select(WeightLog).where(WeightLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="체중 기록을 찾을 수 없습니다.")
    log.log_date = data.log_date
    log.weight_kg = data.weight_kg
    log.body_fat_pct = data.body_fat_pct
    await db.flush()
    await db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=204)
async def delete_weight_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """체중 기록을 삭제합니다."""
    result = await db.execute(select(WeightLog).where(WeightLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="체중 기록을 찾을 수 없습니다.")
    await db.delete(log)
