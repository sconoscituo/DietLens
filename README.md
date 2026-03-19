# DietLens - AI 식단 트래커

> Gemini AI로 음식 사진을 분석해 칼로리를 자동 계산하는 식단 관리 앱

## 소개

DietLens는 음식 사진 한 장으로 칼로리와 영양 정보를 즉시 파악할 수 있는 AI 기반 식단 트래커입니다. Google Gemini Vision API를 활용해 사진 속 음식을 인식하고, 칼로리·탄수화물·단백질·지방을 자동으로 계산합니다.

## 주요 기능

- 음식 사진 업로드 → Gemini AI 자동 분석
- 칼로리 및 3대 영양소 자동 계산
- 하루/주간/월간 식단 기록 및 리포트
- 목표 칼로리 설정 및 달성률 추적
- 수분 섭취 및 운동 기록
- 한국 음식 영양 DB 내장

## 수익 구조

| 플랜 | 가격 | 분석 횟수 | 기능 |
|------|------|-----------|------|
| 무료 | 0원 | 하루 5회 | 기본 칼로리 분석 |
| 프리미엄 | 월 9,900원 | 무제한 | 칼로리 분석 + 주간 리포트 + 영양 코칭 |

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, Python 3.11 |
| Database | SQLite (aiosqlite) |
| AI | Google Gemini API |
| 인증 | JWT |
| 배포 | Docker, Docker Compose |

## 설치 및 실행

### 사전 요구사항

- Python 3.11+
- Docker (선택)
- Google Gemini API 키

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/your-username/DietLens.git
cd DietLens

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Docker 실행

```bash
docker-compose up -d
```

서버 실행 후 http://localhost:8000 접속

## 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 메인 페이지 |
| `POST` | `/api/analysis/image` | 음식 사진 분석 (칼로리 자동 계산) |
| `GET` | `/api/meals` | 식사 기록 목록 조회 |
| `POST` | `/api/meals` | 식사 기록 추가 |
| `GET` | `/api/meals/{id}` | 식사 기록 상세 조회 |
| `DELETE` | `/api/meals/{id}` | 식사 기록 삭제 |
| `GET` | `/api/foods` | 음식 DB 검색 |
| `GET` | `/api/goals` | 목표 칼로리 조회 |
| `PUT` | `/api/goals` | 목표 칼로리 설정 |
| `GET` | `/api/reports/daily` | 일간 리포트 |
| `GET` | `/api/reports/weekly` | 주간 리포트 (프리미엄) |
| `POST` | `/api/water` | 수분 섭취 기록 |
| `POST` | `/api/exercise` | 운동 기록 추가 |

## 구독 플랜 비교

| 기능 | 무료 | 프리미엄 |
|------|:----:|:--------:|
| AI 사진 분석 | 하루 5회 | 무제한 |
| 칼로리 트래킹 | O | O |
| 음식 DB 검색 | O | O |
| 일간 리포트 | O | O |
| 주간 리포트 | X | O |
| 영양 코칭 | X | O |
| 데이터 내보내기 | X | O |

## 환경 변수

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite+aiosqlite:///./dietlens.db
```

## 라이선스

MIT
