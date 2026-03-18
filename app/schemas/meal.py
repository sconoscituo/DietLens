# 식사 스키마
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MealItemCreate(BaseModel):
    food_id: Optional[int] = Field(None, description="음식 DB ID (없으면 직접 입력)")
    food_name: str = Field(..., description="음식명")
    amount: float = Field(100.0, description="섭취량 (g)")
    calories: float = Field(0.0, description="칼로리")
    carbohydrates: float = Field(0.0, description="탄수화물")
    protein: float = Field(0.0, description="단백질")
    fat: float = Field(0.0, description="지방")


class MealItemResponse(BaseModel):
    id: int
    food_id: Optional[int]
    food_name: str
    amount: float
    calories: float
    carbohydrates: float
    protein: float
    fat: float

    class Config:
        from_attributes = True


class MealCreate(BaseModel):
    meal_date: str = Field(..., description="식사 날짜 (YYYY-MM-DD)")
    meal_type: str = Field(..., description="식사 종류 (아침/점심/저녁/간식)")
    items: List[MealItemCreate] = Field(default_factory=list)
    notes: Optional[str] = None


class MealResponse(BaseModel):
    id: int
    meal_date: str
    meal_type: str
    total_calories: float
    total_carbohydrates: float
    total_protein: float
    total_fat: float
    image_path: Optional[str]
    ai_analysis: Optional[str]
    notes: Optional[str]
    items: List[MealItemResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailyNutrition(BaseModel):
    """일별 영양 집계"""
    date: str
    total_calories: float
    total_carbohydrates: float
    total_protein: float
    total_fat: float
    meal_count: int
    meals: List[MealResponse] = []


class GoalCreate(BaseModel):
    goal_type: str = Field("유지", description="다이어트/벌크업/유지")
    daily_calories: float = Field(2000.0, description="일일 목표 칼로리")
    daily_carbohydrates: float = Field(250.0, description="탄수화물 목표 (g)")
    daily_protein: float = Field(60.0, description="단백질 목표 (g)")
    daily_fat: float = Field(55.0, description="지방 목표 (g)")
    weight: Optional[float] = None
    target_weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_level: str = "보통"


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    daily_calories: float
    daily_carbohydrates: float
    daily_protein: float
    daily_fat: float
    weight: Optional[float]
    target_weight: Optional[float]
    height: Optional[float]
    age: Optional[int]
    gender: Optional[str]
    activity_level: str
    is_active: bool

    class Config:
        from_attributes = True


class AIAnalysisResult(BaseModel):
    """AI 음식 분석 결과"""
    foods: List[dict]
    total_calories: float
    total_carbohydrates: float
    total_protein: float
    total_fat: float
    analysis_text: str
    confidence: str = "보통"
