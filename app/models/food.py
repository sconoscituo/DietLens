# 음식 데이터베이스 모델
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Food(Base):
    """음식 정보 테이블"""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)          # 음식명
    name_en = Column(String(200), nullable=True)                    # 영문명
    category = Column(String(100), nullable=True)                   # 카테고리 (밥류, 국류 등)
    serving_size = Column(Float, default=100.0)                     # 1회 제공량 (g)
    serving_unit = Column(String(20), default="g")                  # 단위
    calories = Column(Float, nullable=False)                        # 칼로리 (kcal)
    carbohydrates = Column(Float, default=0.0)                      # 탄수화물 (g)
    protein = Column(Float, default=0.0)                            # 단백질 (g)
    fat = Column(Float, default=0.0)                                # 지방 (g)
    fiber = Column(Float, default=0.0)                              # 식이섬유 (g)
    sodium = Column(Float, default=0.0)                             # 나트륨 (mg)
    sugar = Column(Float, default=0.0)                              # 당류 (g)
    is_favorite = Column(Boolean, default=False)                    # 즐겨찾기
    is_custom = Column(Boolean, default=False)                      # 사용자 추가 음식
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    meal_items = relationship("MealItem", back_populates="food")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "category": self.category,
            "serving_size": self.serving_size,
            "serving_unit": self.serving_unit,
            "calories": self.calories,
            "carbohydrates": self.carbohydrates,
            "protein": self.protein,
            "fat": self.fat,
            "fiber": self.fiber,
            "sodium": self.sodium,
            "sugar": self.sugar,
            "is_favorite": self.is_favorite,
        }
