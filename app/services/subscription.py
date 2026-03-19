"""구독 플랜 관리"""
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"   # 월 7,900원
    FAMILY = "family"     # 월 14,900원 (최대 4인)

PLAN_LIMITS = {
    PlanType.FREE:    {"scans_per_day": 3,  "ai_meal_plan": False, "nutrition_report": False},
    PlanType.PREMIUM: {"scans_per_day": 50, "ai_meal_plan": True,  "nutrition_report": True},
    PlanType.FAMILY:  {"scans_per_day": 200,"ai_meal_plan": True,  "nutrition_report": True},
}

PLAN_PRICES_KRW = {
    PlanType.FREE: 0,
    PlanType.PREMIUM: 7900,
    PlanType.FAMILY: 14900,
}

def get_plan_limits(plan: PlanType) -> dict:
    return PLAN_LIMITS[plan]

def get_plan_price(plan: PlanType) -> int:
    return PLAN_PRICES_KRW[plan]
