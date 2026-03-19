# DietLens - AI 식단 분석 트래커

## 필요한 API 키 및 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 (음식 이미지 분석용) | https://aistudio.google.com/app/apikey |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |
| `UPLOAD_DIR` | 업로드 파일 저장 디렉토리 (기본: `uploads`) | - |

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/DietLens.git
cd DietLens

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# GEMINI_API_KEY=your_gemini_api_key

# 5. 업로드 디렉토리 생성
mkdir -p uploads

# 6. 서버 실행
uvicorn app.main:app --reload
```

서버 기동 후 http://localhost:8000 에서 웹 UI를, http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

## Docker로 실행

```bash
docker-compose up --build
```

## 주요 기능 사용법

### 음식 이미지 분석
- 음식 사진을 업로드하면 Gemini AI가 식품을 인식하고 영양소(칼로리, 탄수화물, 단백질, 지방)를 자동 분석합니다.
- 지원 이미지 형식: `jpg`, `jpeg`, `png`, `webp`, `heic`
- 최대 파일 크기: 10MB

### 식단 기록 관리
- 하루 섭취한 음식을 기록하고 누적 영양소 통계를 확인합니다.
- 목표 칼로리 대비 실제 섭취량을 시각화해서 볼 수 있습니다.

### 영양 분석 리포트
- 주간/월간 식단 패턴을 분석하여 영양 불균형을 감지합니다.
- AI가 식단 개선 제안을 제공합니다.

## 파일 업로드 제한 사항

- 허용 확장자: `.jpg`, `.jpeg`, `.png`, `.webp`, `.heic`
- 최대 크기: **10MB**
- 업로드된 파일은 `uploads/` 디렉토리에 저장됩니다.

## 프로젝트 구조

```
DietLens/
├── app/
│   ├── config.py       # 환경변수 및 업로드 설정
│   ├── database.py     # DB 연결 관리
│   ├── main.py         # FastAPI 앱 진입점
│   ├── data/           # 식품 영양 데이터
│   ├── models/         # SQLAlchemy 모델
│   ├── routers/        # API 라우터
│   ├── schemas/        # Pydantic 스키마
│   ├── services/       # AI 분석 서비스
│   ├── static/         # 정적 파일 (CSS, JS)
│   └── templates/      # Jinja2 HTML 템플릿
├── uploads/            # 업로드된 이미지 저장소
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
