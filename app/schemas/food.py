# 음식 스키마
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FoodBase(BaseModel):
    name: str = Field(..., description="음식명")
    name_en: Optional[str] = Field(None, description="영문명")
    category: Optional[str] = Field(None, description="카테고리")
    serving_size: float = Field(100.0, description="1회 제공량 (g)")
    serving_unit: str = Field("g", description="단위")
    calories: float = Field(..., description="칼로리 (kcal)")
    carbohydrates: float = Field(0.0, description="탄수화물 (g)")
    protein: float = Field(0.0, description="단백질 (g)")
    fat: float = Field(0.0, description="지방 (g)")
    fiber: float = Field(0.0, description="식이섬유 (g)")
    sodium: float = Field(0.0, description="나트륨 (mg)")
    sugar: float = Field(0.0, description="당류 (g)")


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[float] = None
    carbohydrates: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    is_favorite: Optional[bool] = None


class FoodResponse(FoodBase):
    id: int
    is_favorite: bool
    is_custom: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FoodSearchResult(BaseModel):
    """음식 검색 결과"""
    id: int
    name: str
    category: Optional[str]
    calories: float
    carbohydrates: float
    protein: float
    fat: float
    serving_size: float
    serving_unit: str
    is_favorite: bool

    class Config:
        from_attributes = True
