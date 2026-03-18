# 식사 기록 CRUD 라우터
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.database import get_db
from app.models.meal import Meal, MealItem
from app.models.food import Food
from app.schemas.meal import MealCreate, MealResponse
from app.services.nutrition import update_daily_log, scale_nutrition
from datetime import date

router = APIRouter(prefix="/api/meals", tags=["식사 기록"])


@router.get("/", response_model=List[MealResponse])
async def get_meals(
    meal_date: Optional[str] = Query(None, description="날짜 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """식사 기록 목록을 반환합니다."""
    query = select(Meal).options(selectinload(Meal.items))
    if meal_date:
        query = query.where(Meal.meal_date == meal_date)
    query = query.order_by(Meal.meal_date.desc(), Meal.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    """특정 식사 기록을 반환합니다."""
    result = await db.execute(
        select(Meal).options(selectinload(Meal.items)).where(Meal.id == meal_id)
    )
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=404, detail="식사 기록을 찾을 수 없습니다.")
    return meal


@router.post("/", response_model=MealResponse, status_code=201)
async def create_meal(data: MealCreate, db: AsyncSession = Depends(get_db)):
    """새 식사를 기록합니다."""
    # 같은 날짜, 같은 타입 식사가 있으면 항목 추가
    result = await db.execute(
        select(Meal).options(selectinload(Meal.items)).where(
            and_(Meal.meal_date == data.meal_date, Meal.meal_type == data.meal_type)
        )
    )
    meal = result.scalar_one_or_none()

    if not meal:
        meal = Meal(
            meal_date=data.meal_date,
            meal_type=data.meal_type,
            notes=data.notes,
        )
        db.add(meal)
        await db.flush()

    # 식품 항목 추가
    for item_data in data.items:
        # food_id가 있으면 DB에서 영양정보 가져와 비례 계산
        if item_data.food_id:
            food_result = await db.execute(select(Food).where(Food.id == item_data.food_id))
            food = food_result.scalar_one_or_none()
            if food:
                scaled = scale_nutrition(food.to_dict(), item_data.amount)
                item = MealItem(
                    meal_id=meal.id,
                    food_id=item_data.food_id,
                    food_name=food.name,
                    amount=item_data.amount,
                    **scaled,
                )
            else:
                item = MealItem(meal_id=meal.id, **item_data.model_dump())
        else:
            item = MealItem(meal_id=meal.id, **item_data.model_dump())

        db.add(item)

    await db.flush()

    # 식사 합계 재계산
    await db.refresh(meal, ["items"])
    meal.total_calories = sum(i.calories for i in meal.items)
    meal.total_carbohydrates = sum(i.carbohydrates for i in meal.items)
    meal.total_protein = sum(i.protein for i in meal.items)
    meal.total_fat = sum(i.fat for i in meal.items)

    await db.flush()

    # 일별 집계 갱신
    await update_daily_log(db, data.meal_date)
    await db.refresh(meal)

    return meal


@router.delete("/{meal_id}", status_code=204)
async def delete_meal(meal_id: int, db: AsyncSession = Depends(get_db)):
    """식사 기록을 삭제합니다."""
    result = await db.execute(select(Meal).where(Meal.id == meal_id))
    meal = result.scalar_one_or_none()
    if not meal:
        raise HTTPException(status_code=404, detail="식사 기록을 찾을 수 없습니다.")
    meal_date = meal.meal_date
    await db.delete(meal)
    await db.flush()
    await update_daily_log(db, meal_date)


@router.delete("/{meal_id}/items/{item_id}", status_code=204)
async def delete_meal_item(meal_id: int, item_id: int, db: AsyncSession = Depends(get_db)):
    """식사 항목을 삭제합니다."""
    result = await db.execute(
        select(MealItem).where(and_(MealItem.id == item_id, MealItem.meal_id == meal_id))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")

    meal_result = await db.execute(
        select(Meal).options(selectinload(Meal.items)).where(Meal.id == meal_id)
    )
    meal = meal_result.scalar_one_or_none()

    await db.delete(item)
    await db.flush()

    if meal:
        await db.refresh(meal, ["items"])
        meal.total_calories = sum(i.calories for i in meal.items)
        meal.total_carbohydrates = sum(i.carbohydrates for i in meal.items)
        meal.total_protein = sum(i.protein for i in meal.items)
        meal.total_fat = sum(i.fat for i in meal.items)
        await db.flush()
        await update_daily_log(db, meal.meal_date)
