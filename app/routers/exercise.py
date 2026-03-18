# 운동 기록 + 소모 칼로리 라우터
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from app.database import get_db
from app.models.exercise import Exercise

router = APIRouter(prefix="/api/exercise", tags=["운동 기록"])

# MET 값 기반 한국인 자주 하는 운동 목록
# 소모 칼로리 = MET × 체중(kg) × 시간(h)
# 기본 체중 70kg 기준 1분당 kcal = MET × 70 / 60
EXERCISE_LIST = [
    {"name": "걷기",     "met": 3.5,  "icon": "🚶"},
    {"name": "빠르게걷기", "met": 4.5, "icon": "🚶‍♂️"},
    {"name": "달리기",   "met": 8.0,  "icon": "🏃"},
    {"name": "자전거",   "met": 6.0,  "icon": "🚴"},
    {"name": "수영",     "met": 7.0,  "icon": "🏊"},
    {"name": "웨이트",   "met": 5.0,  "icon": "🏋️"},
    {"name": "등산",     "met": 7.5,  "icon": "⛰️"},
    {"name": "요가",     "met": 2.5,  "icon": "🧘"},
    {"name": "줄넘기",   "met": 10.0, "icon": "🪃"},
    {"name": "배드민턴", "met": 5.5,  "icon": "🏸"},
    {"name": "축구",     "met": 7.0,  "icon": "⚽"},
    {"name": "농구",     "met": 6.5,  "icon": "🏀"},
    {"name": "테니스",   "met": 6.0,  "icon": "🎾"},
    {"name": "필라테스", "met": 3.0,  "icon": "🤸"},
    {"name": "댄스",     "met": 4.5,  "icon": "💃"},
    {"name": "태권도",   "met": 7.0,  "icon": "🥋"},
]

# 운동명 → MET 딕셔너리
_MET_MAP = {e["name"]: e["met"] for e in EXERCISE_LIST}


def calc_calories(exercise_type: str, duration_min: int, weight_kg: float = 70.0) -> float:
    """MET 기반 소모 칼로리를 계산합니다. (기본 체중 70kg)"""
    met = _MET_MAP.get(exercise_type, 4.0)
    return round(met * weight_kg * (duration_min / 60), 1)


class ExerciseCreate(BaseModel):
    exercise_date: str = Field(..., description="운동 날짜 (YYYY-MM-DD)")
    exercise_type: str = Field(..., description="운동 종류")
    duration_min: int = Field(..., ge=1, le=600, description="운동 시간 (분)")
    weight_kg: float = Field(70.0, ge=20, le=300, description="체중 (kg, 칼로리 계산용)")
    memo: Optional[str] = Field(None, max_length=200)


class ExerciseResponse(BaseModel):
    id: int
    exercise_date: str
    exercise_type: str
    duration_min: int
    calories_burned: float
    memo: Optional[str]

    class Config:
        from_attributes = True


class ExerciseSummary(BaseModel):
    exercise_date: str
    total_calories_burned: float
    total_duration_min: int
    records: List[ExerciseResponse]


@router.get("/types")
async def get_exercise_types():
    """지원하는 운동 종류 목록을 반환합니다."""
    return EXERCISE_LIST


@router.post("/calc-calories")
async def calculate_calories(exercise_type: str, duration_min: int, weight_kg: float = 70.0):
    """운동 종류, 시간, 체중으로 소모 칼로리를 계산합니다."""
    calories = calc_calories(exercise_type, duration_min, weight_kg)
    met = _MET_MAP.get(exercise_type, 4.0)
    return {
        "exercise_type": exercise_type,
        "duration_min": duration_min,
        "weight_kg": weight_kg,
        "met": met,
        "calories_burned": calories,
    }


@router.post("/", response_model=ExerciseResponse, status_code=201)
async def create_exercise(data: ExerciseCreate, db: AsyncSession = Depends(get_db)):
    """운동 기록을 저장합니다."""
    calories = calc_calories(data.exercise_type, data.duration_min, data.weight_kg)
    exercise = Exercise(
        exercise_date=data.exercise_date,
        exercise_type=data.exercise_type,
        duration_min=data.duration_min,
        calories_burned=calories,
        memo=data.memo,
    )
    db.add(exercise)
    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.get("/summary/{target_date}", response_model=ExerciseSummary)
async def get_exercise_summary(target_date: str, db: AsyncSession = Depends(get_db)):
    """특정 날짜의 운동 현황을 반환합니다."""
    result = await db.execute(
        select(Exercise)
        .where(Exercise.exercise_date == target_date)
        .order_by(Exercise.created_at)
    )
    records = result.scalars().all()
    total_calories = round(sum(r.calories_burned for r in records), 1)
    total_duration = sum(r.duration_min for r in records)
    return ExerciseSummary(
        exercise_date=target_date,
        total_calories_burned=total_calories,
        total_duration_min=total_duration,
        records=records,
    )


@router.get("/", response_model=List[ExerciseResponse])
async def list_exercises(
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """날짜 범위의 운동 기록 목록을 반환합니다."""
    result = await db.execute(
        select(Exercise)
        .where(Exercise.exercise_date >= start_date, Exercise.exercise_date <= end_date)
        .order_by(Exercise.exercise_date.desc(), Exercise.created_at.desc())
    )
    return result.scalars().all()


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int, data: ExerciseCreate, db: AsyncSession = Depends(get_db)
):
    """운동 기록을 수정합니다."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="운동 기록을 찾을 수 없습니다.")
    exercise.exercise_date = data.exercise_date
    exercise.exercise_type = data.exercise_type
    exercise.duration_min = data.duration_min
    exercise.calories_burned = calc_calories(data.exercise_type, data.duration_min, data.weight_kg)
    exercise.memo = data.memo
    await db.flush()
    await db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(exercise_id: int, db: AsyncSession = Depends(get_db)):
    """운동 기록을 삭제합니다."""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="운동 기록을 찾을 수 없습니다.")
    await db.delete(exercise)
