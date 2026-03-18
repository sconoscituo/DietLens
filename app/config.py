# 앱 설정
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API 키
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# 데이터베이스 URL
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dietlens.db")

# 업로드 디렉토리
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

# 최대 파일 크기 (10MB)
MAX_FILE_SIZE: int = 10 * 1024 * 1024

# 허용 이미지 형식
ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "webp", "heic"}

# 앱 기본 설정
APP_TITLE: str = "DietLens - AI 식단 트래커"
APP_VERSION: str = "1.0.0"
