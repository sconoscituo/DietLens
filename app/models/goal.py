# 목표 설정 모델
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Goal(Base):
    """사용자 목표 설정 테이블"""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    goal_type = Column(String(20), nullable=False, default="유지")   # 다이어트/벌크업/유지
    daily_calories = Column(Float, nullable=False, default=2000.0)   # 일일 목표 칼로리
    daily_carbohydrates = Column(Float, default=250.0)               # 탄수화물 목표 (g)
    daily_protein = Column(Float, default=60.0)                      # 단백질 목표 (g)
    daily_fat = Column(Float, default=55.0)                          # 지방 목표 (g)
    weight = Column(Float, nullable=True)                            # 현재 체중 (kg)
    target_weight = Column(Float, nullable=True)                     # 목표 체중 (kg)
    height = Column(Float, nullable=True)                            # 키 (cm)
    age = Column(Integer, nullable=True)                             # 나이
    gender = Column(String(10), nullable=True)                       # 성별
    activity_level = Column(String(20), default="보통")              # 활동량
    is_active = Column(Boolean, default=True)                        # 현재 활성 목표
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def calculate_bmr(self) -> float:
        """기초대사량 계산 (Mifflin-St Jeor 공식)"""
        if not all([self.weight, self.height, self.age, self.gender]):
            return self.daily_calories
        if self.gender == "남성":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return bmr

    def calculate_tdee(self) -> float:
        """일일 총 에너지 소비량 계산"""
        activity_multipliers = {
            "거의없음": 1.2,
            "가벼움": 1.375,
            "보통": 1.55,
            "활발함": 1.725,
            "매우활발함": 1.9,
        }
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return self.calculate_bmr() * multiplier
