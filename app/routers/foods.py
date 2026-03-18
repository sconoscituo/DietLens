# 음식 DB 관리 라우터
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional
import httpx
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


@router.post("/barcode")
async def lookup_barcode(barcode: str = Query(..., description="바코드 번호")):
    """
    바코드 번호로 Open Food Facts API에서 영양 정보를 조회합니다.
    결과를 DietLens 음식 형식으로 변환하여 반환합니다.
    """
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers={"User-Agent": "DietLens/1.0"})
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="바코드 정보를 찾을 수 없습니다.")

        data = resp.json()
        if data.get("status") != 1:
            raise HTTPException(status_code=404, detail="해당 바코드의 제품 정보가 없습니다.")

        product = data.get("product", {})
        nutriments = product.get("nutriments", {})

        # 제품명: 한국어 우선, 없으면 영문명
        name = (
            product.get("product_name_ko")
            or product.get("product_name")
            or product.get("product_name_en")
            or "알 수 없는 제품"
        )
        serving_size = float(product.get("serving_size_imported") or 100)

        # Open Food Facts 영양 필드 (100g 기준)
        calories = float(nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal") or 0)
        carbs = float(nutriments.get("carbohydrates_100g") or nutriments.get("carbohydrates") or 0)
        protein = float(nutriments.get("proteins_100g") or nutriments.get("proteins") or 0)
        fat = float(nutriments.get("fat_100g") or nutriments.get("fat") or 0)
        fiber = float(nutriments.get("fiber_100g") or nutriments.get("fiber") or 0)
        sodium = float(nutriments.get("sodium_100g") or nutriments.get("sodium") or 0) * 1000  # g → mg

        return {
            "barcode": barcode,
            "name": name,
            "name_en": product.get("product_name_en") or product.get("product_name"),
            "brand": product.get("brands", ""),
            "category": product.get("categories_tags", [""])[0].replace("en:", "").replace("-", " ") if product.get("categories_tags") else "",
            "serving_size": 100.0,
            "serving_unit": "g",
            "calories": round(calories, 1),
            "carbohydrates": round(carbs, 1),
            "protein": round(protein, 1),
            "fat": round(fat, 1),
            "fiber": round(fiber, 1),
            "sodium": round(sodium, 1),
            "image_url": product.get("image_front_small_url") or product.get("image_url") or "",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"바코드 조회 중 오류가 발생했습니다: {str(e)}")
