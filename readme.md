# 📝 Global CapFlow

**AI-Powered Market Insight Archiver & Trend Analyzer**

시가총액 상위 기업들의 순위 변화, 재무/뉴스 데이터, AI 분석을 한곳에 아카이빙해 “오늘의 뉴스가 미래의 역사”가 되도록 만드는 서비스입니다. DB-First 아키텍처를 중심으로, 외부 링크가 사라져도 핵심 요약과 출처가 남는 신뢰성 있는 투자 히스토리를 제공합니다.

---

## 무엇을 할 수 있나요?
- **연도별 글로벌 시총 TOP 랭킹**: 2015~현재까지 연도별 TOP 100, 신규 진입/이탈 기업 비교, Bump 차트용 히스토리 제공.
- **기업 프로필 & 가격 히스토리**: 티커 상세 조회, 로고/섹터/국가/재무 지표, 가격 히스토리 조회 및 필요 시 실시간 수집.
- **AI 투자 리포트**: 뉴스 + 최신 재무 데이터를 결합한 요약/감성 점수 저장. 중복/캐시 처리로 24시간 내 재활용.
- **기업 간 Matchup**: 두 기업을 선택해 AI가 종합 비교 리포트 및 승자 판단. 요청 조합별 24시간 캐시.
- **시장 분위기 스냅샷**: 섹터 트렌드 최신판을 조회하고, 상승 섹터/주도 섹터와 AI 분석 텍스트를 받아볼 수 있음.
- **자동 수집 파이프라인**: 글로벌 Top 100을 DuckDuckGo + yfinance로 모으고 DB에 반영(회사/랭킹/가격).

---

## 아키텍처 개요
| 영역 | 기술 | 핵심 포인트 |
| :--- | :--- | :--- |
| Frontend | React + Vite, Tailwind CSS | 단일 페이지 네비게이션, 랭킹/프로필/비교 UI |
| Backend | FastAPI (async) | CORS 허용, 라우터 분리(rankings, companies, analyze, collection) |
| DB | PostgreSQL | companies / rankings / financials / market_reports / prices / ai_analysis |
| Data Source | yfinance, DuckDuckGo | 시가총액·재무·뉴스 수집 |
| AI | OpenAI GPT-4o | 뉴스 요약, 감성 점수, 비교 리포트 |
| Scheduler | APScheduler | 수집/검증 작업 자동 실행 (lifespan 훅에서 시작/종료) |

### 데이터 파이프라인
1. **Collect**: DuckDuckGo 뉴스, yfinance 재무/시총/가격 수집. 글로벌 TOP 100 랭킹 생성.
2. **Process & AI**: 뉴스 원문을 요약하고 감성 점수 부여. 재무 데이터와 함께 종합 리포트 생성.
3. **Cache & Dedup**: 티커·날짜·요청 해시 단위로 24시간 캐시/업데이트하여 불필요 호출 최소화.
4. **Store**: 핵심 요약, sentiment, 출처 URL, 수집 시각, 가격 히스토리, 랭킹 변동을 DB에 저장.

---

## 주요 API
- `GET /health` : 서비스 상태 체크.
- 수집 파이프라인  
  - `POST /collections/global-top-100` : 글로벌 시총 Top 100 수집 및 DB 반영.
- 랭킹  
  - `GET /rankings/{year}?limit=100` : 특정 연도 Top N.  
  - `GET /rankings/history?limit=10` : 최신 연도 Top N의 연도별 히스토리.  
  - `GET /rankings/movers/latest` : 최신 연도 대비 신규 진입/이탈 리스트.
- 기업/가격  
  - `GET /companies/{ticker}` : 기업 상세 조회.  
  - `POST /companies/{ticker}/fetch` : 재무+뉴스를 즉시 수집 후 저장.  
  - `GET /companies/{ticker}/prices?limit=…` : 가격 히스토리.
- AI 분석  
  - `GET /analyze/market/trends` : 최신 섹터 트렌드 스냅샷.  
  - `POST /analyze/matchup` : 다중 티커 비교 리포트(24h 캐시).

Swagger UI는 `http://localhost:8000/docs` 에서 확인 가능합니다.

---

## 리포지토리 구조 (요약)
- `backend/app/main.py` : FastAPI 엔트리포인트, CORS, lifespan에 스케줄러 연결.
- `backend/app/routers/` : `rankings.py`, `company.py`, `analyze.py`, `collection.py` 등 라우터.
- `backend/app/services/` : 수집/AI/스케줄러/뉴스/시세 로직.
- `backend/migrations/` : DB 스키마 변경 SQL.
- `frontend/src/` : React 컴포넌트(`RankingPage`, `RankingListPage`, `ComparisonPage`, `StockProfilePage` 등)와 API 클라이언트.

---

## 빠른 시작
### 1) Backend (FastAPI)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# .env 예시
set DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
set OPENAI_API_KEY=sk-...

# DB 초기화
python app/create_db.py          # 테이블 생성
# 필요 시 추가 마이그레이션
# psql $DATABASE_URL -f migrations/add_new_fields.sql

# DB 데이터 수집 테스트
python backend/test/test_full_process.py

# 서버 실행
uvicorn app.main:app --reload --app-dir .
```

### 2) Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev -- --host --port 5173
```
환경 변수: `VITE_API_BASE` (기본 `http://localhost:8000`)

---

## 개발 메모
- **테스트**: `backend/test/`에 파이프라인/스케줄러/매치업 등 단위·통합 테스트가 준비되어 있습니다. `pytest`로 실행.
- **캐시/스토리지**: DuckDuckGo·yfinance 캐시용 SQLite(`duckduckgo_news_cache.sqlite`, `yfinance_cache.sqlite`)와 wiki 캐시를 사용.
- **스케줄러**: 앱 기동 시 시작, 종료 시 정리. 필요하면 `app/services/scheduler_service.py`에서 주기 조정.

---

## 로드맵 (요약)
- v1.0: 글로벌 시총 상위 100개 기업 일일 수집/분석.
- v1.1: AI 요약 검증 강화, 파이프라인 안정화.
- v1.5: 주식 외 소셜/밈 등 비정형 데이터 확장.
- v2.0: 유료 데이터 소스(FMP 등) 연동으로 품질 고도화.

