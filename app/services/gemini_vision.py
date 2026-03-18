# Gemini Vision API를 이용한 음식 인식 서비스
import json
import base64
from pathlib import Path
from typing import Optional
import google.generativeai as genai
from PIL import Image
from app.config import GEMINI_API_KEY

# Gemini 설정
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


FOOD_ANALYSIS_PROMPT = """
이 음식 사진을 분석하여 JSON 형식으로 영양 정보를 제공해주세요.

사진에서 보이는 모든 음식을 식별하고, 각 음식의 예상 영양 정보를 제공해주세요.
한국 음식이 포함된 경우 정확한 한국식 이름을 사용해주세요.

반드시 아래 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{
  "foods": [
    {
      "name": "음식명",
      "amount": 예상_섭취량_숫자(g),
      "calories": 칼로리_숫자(kcal),
      "carbohydrates": 탄수화물_숫자(g),
      "protein": 단백질_숫자(g),
      "fat": 지방_숫자(g)
    }
  ],
  "total_calories": 총_칼로리_숫자,
  "total_carbohydrates": 총_탄수화물_숫자,
  "total_protein": 총_단백질_숫자,
  "total_fat": 총_지방_숫자,
  "analysis_text": "음식에 대한 한국어 설명 (2-3문장)",
  "confidence": "높음/보통/낮음"
}

주의사항:
- 모든 수치는 숫자(float)여야 합니다
- 음식이 명확하지 않으면 confidence를 "낮음"으로 설정하세요
- 영양 정보는 일반적인 한국 성인 1인분 기준으로 추정해주세요
"""


async def analyze_food_image(image_path: str) -> dict:
    """
    음식 이미지를 Gemini Vision API로 분석합니다.

    Args:
        image_path: 이미지 파일 경로

    Returns:
        AI 분석 결과 딕셔너리
    """
    if not GEMINI_API_KEY:
        # API 키가 없는 경우 데모 응답 반환
        return _get_demo_response()

    try:
        # 이미지 로드 (컨텍스트 매니저로 파일 디스크립터 누수 방지)
        with Image.open(image_path) as img:
            img.load()  # 파일을 메모리에 완전히 로드한 뒤 닫기 위해 copy
            img_copy = img.copy()

        # Gemini 모델 초기화 (Vision 지원 모델)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # 분석 요청 (비동기 호출로 이벤트 루프 블로킹 방지)
        response = await model.generate_content_async([FOOD_ANALYSIS_PROMPT, img_copy])

        # 응답 파싱
        raw_text = response.text.strip()

        # JSON 블록 추출 (마크다운 코드 블록 처리)
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        result = json.loads(raw_text)

        # 필수 필드 검증
        result.setdefault("foods", [])
        result.setdefault("total_calories", 0.0)
        result.setdefault("total_carbohydrates", 0.0)
        result.setdefault("total_protein", 0.0)
        result.setdefault("total_fat", 0.0)
        result.setdefault("analysis_text", "AI 분석이 완료되었습니다.")
        result.setdefault("confidence", "보통")

        return result

    except json.JSONDecodeError:
        # JSON 파싱 실패 시 텍스트 기반 응답
        return {
            "foods": [],
            "total_calories": 0.0,
            "total_carbohydrates": 0.0,
            "total_protein": 0.0,
            "total_fat": 0.0,
            "analysis_text": "이미지에서 음식을 인식했지만 정확한 영양 정보를 추출하지 못했습니다. 수동으로 입력해주세요.",
            "confidence": "낮음",
        }
    except Exception as e:
        return {
            "foods": [],
            "total_calories": 0.0,
            "total_carbohydrates": 0.0,
            "total_protein": 0.0,
            "total_fat": 0.0,
            "analysis_text": f"분석 중 오류가 발생했습니다: {str(e)}",
            "confidence": "낮음",
            "error": str(e),
        }


def _get_demo_response() -> dict:
    """API 키 없을 때 데모 응답"""
    return {
        "foods": [
            {
                "name": "비빔밥 (데모)",
                "amount": 400,
                "calories": 560,
                "carbohydrates": 95.0,
                "protein": 18.0,
                "fat": 12.0,
            }
        ],
        "total_calories": 560,
        "total_carbohydrates": 95.0,
        "total_protein": 18.0,
        "total_fat": 12.0,
        "analysis_text": "⚠️ 데모 모드: GEMINI_API_KEY를 설정하면 실제 AI 분석이 가능합니다. 현재는 샘플 데이터가 표시됩니다.",
        "confidence": "낮음",
    }
