# 음식 DB 관리 라우터
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional
from app.database import get_db
from app.models.food import Food
from app.schemas.food import FoodCreate, FoodResponse, FoodUpdate, FoodSearchResult

router = APIRouter(prefix="/api/foods", tags=["음식 DB"])


@router.get("/search", response_model=List[FoodSearchResult])
async def search_foods(
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """음식명으로 검색합니다."""
    result = await db.execute(
        select(Food)
        .where(or_(Food.name.contains(q), Food.name_en.contains(q)))
        .order_by(Food.is_favorite.desc(), Food.name)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/favorites", response_model=List[FoodSearchResult])
async def get_favorites(db: AsyncSession = Depends(get_db)):
    """즐겨찾기 음식 목록을 반환합니다."""
    result = await db.execute(
        select(Food).where(Food.is_favorite == True).order_by(Food.name)
    )
    return result.scalars().all()


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """카테고리 목록을 반환합니다."""
    result = await db.execute(
        select(Food.category).distinct().where(Food.category.isnot(None))
    )
    categories = [row[0] for row in result.all()]
    return sorted(categories)


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food(food_id: int, db: AsyncSession = Depends(get_db)):
    """특정 음식 정보를 반환합니다."""
    result = await db.execute(select(Food).where(Food.id == food_id))
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(status_code=404, detail="음식을 찾을 수 없습니다.")
    return food


@router.post("/", response_model=FoodResponse, status_code=201)
async def create_food(data: FoodCreate, db: AsyncSession = Depends(get_db)):
    """새 음식을 추가합니다."""
    food = Food(**data.model_dump(), is_custom=True)
    db.add(food)
    await db.flush()
    await db.refresh(food)
    return food


@router.patch("/{food_id}/favorite", response_model=FoodResponse)
async def toggle_favorite(food_id: int, db: AsyncSession = Depends(get_db)):
    """즐겨찾기를 토글합니다."""
    result = await db.execute(select(Food).where(Food.id == food_id))
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(status_code=404, detail="음식을 찾을 수 없습니다.")
    food.is_favorite = not food.is_favorite
    await db.flush()
    await db.refresh(food)
    return food


@router.put("/{food_id}", response_model=FoodResponse)
async def update_food(food_id: int, data: FoodUpdate, db: AsyncSession = Depends(get_db)):
    """음식 정보를 수정합니다."""
    result = await db.execute(select(Food).where(Food.id == food_id))
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(status_code=404, detail="음식을 찾을 수 없습니다.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(food, field, value)
    await db.flush()
    await db.refresh(food)
    return food


@router.delete("/{food_id}", status_code=204)
async def delete_food(food_id: int, db: AsyncSession = Depends(get_db)):
    """사용자 추가 음식을 삭제합니다."""
    result = await db.execute(select(Food).where(Food.id == food_id, Food.is_custom == True))
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(status_code=404, detail="삭제할 수 없는 음식입니다.")
    await db.delete(food)
