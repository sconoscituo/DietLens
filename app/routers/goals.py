# 목표 설정 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.goal import Goal
from app.schemas.meal import GoalCreate, GoalResponse

router = APIRouter(prefix="/api/goals", tags=["목표 설정"])


@router.get("/current", response_model=GoalResponse)
async def get_current_goal(db: AsyncSession = Depends(get_db)):
    """현재 활성 목표를 반환합니다."""
    result = await db.execute(
        select(Goal).where(Goal.is_active == True).order_by(Goal.id.desc()).limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="설정된 목표가 없습니다.")
    return goal


@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(data: GoalCreate, db: AsyncSession = Depends(get_db)):
    """새 목표를 설정합니다. 기존 목표는 비활성화됩니다."""
    # 기존 목표 비활성화
    result = await db.execute(select(Goal).where(Goal.is_active == True))
    for old_goal in result.scalars().all():
        old_goal.is_active = False

    # 새 목표 생성
    goal = Goal(**data.model_dump(), is_active=True)
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(goal_id: int, data: GoalCreate, db: AsyncSession = Depends(get_db)):
    """목표를 수정합니다."""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")

    for field, value in data.model_dump().items():
        setattr(goal, field, value)
    await db.flush()
    await db.refresh(goal)
    return goal


@router.get("/calculate")
async def calculate_recommended_goal(
    weight: float,
    height: float,
    age: int,
    gender: str,
    activity_level: str = "보통",
    goal_type: str = "유지",
):
    """신체 정보를 기반으로 권장 목표 칼로리를 계산합니다."""
    # BMR 계산 (Mifflin-St Jeor)
    if gender == "남성":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        "거의없음": 1.2,
        "가벼움": 1.375,
        "보통": 1.55,
        "활발함": 1.725,
        "매우활발함": 1.9,
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    # 목표에 따른 칼로리 조정
    if goal_type == "다이어트":
        target_calories = tdee * 0.8  # 20% 감량
    elif goal_type == "벌크업":
        target_calories = tdee * 1.15  # 15% 증가
    else:
        target_calories = tdee

    # 영양소 비율 (탄:단:지 = 5:3:2)
    carbs = round(target_calories * 0.5 / 4, 1)
    protein = round(target_calories * 0.3 / 4, 1)
    fat = round(target_calories * 0.2 / 9, 1)

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "recommended_calories": round(target_calories, 1),
        "recommended_carbohydrates": carbs,
        "recommended_protein": protein,
        "recommended_fat": fat,
    }
