# 운동 기록 모델
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Exercise(Base):
    """운동 기록 테이블"""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    exercise_date = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    exercise_type = Column(String(50), nullable=False)               # 운동 종류 (걷기, 달리기 등)
    duration_min = Column(Integer, nullable=False)                   # 운동 시간 (분)
    calories_burned = Column(Float, nullable=False, default=0.0)     # 소모 칼로리 (kcal)
    memo = Column(String(200), nullable=True)                        # 메모
    created_at = Column(DateTime(timezone=True), server_default=func.now())
