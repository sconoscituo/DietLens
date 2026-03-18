# 일별 영양 기록 모델
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class DailyLog(Base):
    """일별 영양 집계 테이블"""
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(String(10), nullable=False, unique=True, index=True)  # YYYY-MM-DD
    total_calories = Column(Float, default=0.0)         # 총 칼로리
    total_carbohydrates = Column(Float, default=0.0)    # 총 탄수화물
    total_protein = Column(Float, default=0.0)          # 총 단백질
    total_fat = Column(Float, default=0.0)              # 총 지방
    total_fiber = Column(Float, default=0.0)            # 총 식이섬유
    meal_count = Column(Integer, default=0)             # 식사 횟수
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
