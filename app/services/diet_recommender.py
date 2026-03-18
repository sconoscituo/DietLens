# AI 식단 추천 서비스 (Gemini 기반)
import json
from typing import Optional
import google.generativeai as genai
from app.config import GEMINI_API_KEY

# Gemini 설정
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _build_prompt(
    goal_calories: float,
    consumed_calories: float,
    goal_protein: float,
    consumed_protein: float,
    goal_carbs: float,
    consumed_carbs: float,
    goal_fat: float,
    consumed_fat: float,
    preferred_foods: Optional[str] = None,
) -> str:
    """식단 추천 프롬프트를 생성합니다."""
    remaining_cal = max(0, goal_calories - consumed_calories)
    remaining_protein = max(0, goal_protein - consumed_protein)
    remaining_carbs = max(0, goal_carbs - consumed_carbs)
    remaining_fat = max(0, goal_fat - consumed_fat)

    pref_text = f"\n선호 음식 또는 키워드: {preferred_foods}" if preferred_foods else ""

    return f"""당신은 한국인 영양사입니다. 오늘 식단 데이터를 보고 남은 식사 추천을 JSON으로만 응답해주세요.

[오늘 섭취 현황]
- 섭취 칼로리: {consumed_calories:.0f} kcal / 목표 {goal_calories:.0f} kcal
- 남은 칼로리: {remaining_cal:.0f} kcal
- 단백질: {consumed_protein:.1f}g 섭취 / 목표 {goal_protein:.1f}g (남은 {remaining_protein:.1f}g)
- 탄수화물: {consumed_carbs:.1f}g 섭취 / 목표 {goal_carbs:.1f}g (남은 {remaining_carbs:.1f}g)
- 지방: {consumed_fat:.1f}g 섭취 / 목표 {goal_fat:.1f}g (남은 {remaining_fat:.1f}g){pref_text}

위 상황에 맞게 남은 끼니 또는 간식으로 먹을 수 있는 한국 음식을 추천해주세요.
반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "summary": "현재 식단 상태 한 줄 평가",
  "recommendations": [
    {{
      "meal_type": "점심 또는 저녁 또는 간식",
      "food_name": "음식명",
      "amount": "1인분 기준량",
      "calories": 칼로리_숫자,
      "reason": "이 음식을 추천하는 이유 (영양 관점)"
    }}
  ],
  "tips": "오늘 식단에 대한 영양 팁 (1-2문장)"
}}
"""


async def get_next_meal_recommendation(
    goal_calories: float,
    consumed_calories: float,
    goal_protein: float,
    consumed_protein: float,
    goal_carbs: float,
    consumed_carbs: float,
    goal_fat: float,
    consumed_fat: float,
    preferred_foods: Optional[str] = None,
) -> dict:
    """
    현재 섭취 현황과 목표를 바탕으로 다음 식사를 Gemini AI가 추천합니다.
    API 키가 없으면 규칙 기반 데모 추천을 반환합니다.
    """
    if not GEMINI_API_KEY:
        return _get_demo_recommendation(goal_calories, consumed_calories)

    prompt = _build_prompt(
        goal_calories, consumed_calories,
        goal_protein, consumed_protein,
        goal_carbs, consumed_carbs,
        goal_fat, consumed_fat,
        preferred_foods,
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await model.generate_content_async(prompt)
        raw_text = response.text.strip()

        # 마크다운 코드 블록 제거
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        result = json.loads(raw_text)
        result.setdefault("summary", "오늘의 식단을 분석했습니다.")
        result.setdefault("recommendations", [])
        result.setdefault("tips", "균형 잡힌 식사를 유지하세요.")
        return result

    except json.JSONDecodeError:
        return _get_demo_recommendation(goal_calories, consumed_calories)
    except Exception as e:
        return {
            "summary": f"추천 생성 중 오류가 발생했습니다: {str(e)}",
            "recommendations": [],
            "tips": "잠시 후 다시 시도해주세요.",
        }


def _get_demo_recommendation(goal_calories: float, consumed_calories: float) -> dict:
    """API 키 없을 때 규칙 기반 데모 추천을 반환합니다."""
    remaining = goal_calories - consumed_calories

    if remaining > 600:
        recs = [
            {
                "meal_type": "점심",
                "food_name": "된장찌개 + 잡곡밥",
                "amount": "밥 200g + 찌개 1그릇",
                "calories": 450,
                "reason": "단백질과 발효 식품으로 장 건강에 좋고 칼로리 균형에 적합합니다.",
            },
            {
                "meal_type": "저녁",
                "food_name": "닭가슴살 샐러드",
                "amount": "닭가슴살 150g + 채소",
                "calories": 280,
                "reason": "고단백 저지방으로 남은 칼로리를 효율적으로 채울 수 있습니다.",
            },
        ]
    elif remaining > 200:
        recs = [
            {
                "meal_type": "간식",
                "food_name": "그릭 요거트 + 과일",
                "amount": "요거트 150g + 바나나 1/2개",
                "calories": 180,
                "reason": "단백질과 천연 당분으로 에너지를 보충하기 좋습니다.",
            }
        ]
    else:
        recs = [
            {
                "meal_type": "간식",
                "food_name": "따뜻한 허브차",
                "amount": "1잔",
                "calories": 5,
                "reason": "목표 칼로리에 거의 도달했습니다. 수분 보충을 권장합니다.",
            }
        ]

    return {
        "summary": f"⚠️ 데모 모드 — 오늘 {consumed_calories:.0f}kcal 섭취, {remaining:.0f}kcal 남았습니다.",
        "recommendations": recs,
        "tips": "GEMINI_API_KEY를 설정하면 개인 맞춤 AI 추천을 받을 수 있습니다.",
    }
