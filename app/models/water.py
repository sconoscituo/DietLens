# 물 섭취 기록 모델
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class WaterLog(Base):
    """물 섭취 기록 테이블"""
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_date = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    amount_ml = Column(Integer, nullable=False)                  # 섭취량 (ml)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
