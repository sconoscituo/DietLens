# 체중 기록 모델
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class WeightLog(Base):
    """체중 기록 테이블"""
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(String(10), nullable=False, unique=True, index=True)  # YYYY-MM-DD
    weight_kg = Column(Float, nullable=False)                               # 체중 (kg)
    body_fat_pct = Column(Float, nullable=True)                             # 체지방률 (%, 선택)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
