# 식사 기록 모델
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MealType(str, enum.Enum):
    """식사 종류"""
    BREAKFAST = "아침"
    LUNCH = "점심"
    DINNER = "저녁"
    SNACK = "간식"


class Meal(Base):
    """식사 기록 테이블"""
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_date = Column(String(10), nullable=False, index=True)       # YYYY-MM-DD
    meal_type = Column(String(10), nullable=False)                   # 아침/점심/저녁/간식
    total_calories = Column(Float, default=0.0)                      # 총 칼로리
    total_carbohydrates = Column(Float, default=0.0)                 # 총 탄수화물
    total_protein = Column(Float, default=0.0)                       # 총 단백질
    total_fat = Column(Float, default=0.0)                           # 총 지방
    image_path = Column(String(500), nullable=True)                  # AI 분석 이미지 경로
    ai_analysis = Column(Text, nullable=True)                        # AI 분석 결과 원문
    notes = Column(Text, nullable=True)                              # 메모
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")

    def recalculate_totals(self):
        """식품 항목 기반으로 합계 재계산"""
        self.total_calories = sum(item.calories for item in self.items)
        self.total_carbohydrates = sum(item.carbohydrates for item in self.items)
        self.total_protein = sum(item.protein for item in self.items)
        self.total_fat = sum(item.fat for item in self.items)


class MealItem(Base):
    """식사 항목 테이블 (식사에 포함된 개별 음식)"""
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)  # None이면 AI 인식 음식
    food_name = Column(String(200), nullable=False)                   # 음식명 (직접 저장)
    amount = Column(Float, default=100.0)                             # 섭취량 (g)
    calories = Column(Float, default=0.0)                             # 칼로리
    carbohydrates = Column(Float, default=0.0)                        # 탄수화물
    protein = Column(Float, default=0.0)                              # 단백질
    fat = Column(Float, default=0.0)                                  # 지방
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    meal = relationship("Meal", back_populates="items")
    food = relationship("Food", back_populates="meal_items")
