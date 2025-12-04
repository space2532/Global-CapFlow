# 📝 Global CapFlow

**AI-Powered Market Insight Archiver & Trend Analyzer**

Global CapFlow는 시장의 \*\*정량적 데이터(주가)\*\*와 \*\*정성적 데이터(뉴스, 시장 분위기)\*\*를 매일 수집·분석하여, 시간이 지날수록 가치가 더해지는 \*\*'투자 역사 데이터베이스'\*\*를 구축하는 웹 서비스입니다.

단순한 실시간 주가 나열을 지양하고, \*\*"오늘의 뉴스가 미래의 역사"\*\*라는 관점에서 AI가 데이터를 요약, 검증, 자산화(Assetization)하는 **DB-First 아키텍처**를 채택했습니다. 이를 통해 사용자는 외부 API 장애나 링크 소실(Link Rot) 걱정 없이, 언제든 과거와 현재를 잇는 깊이 있는 인사이트를 조회할 수 있습니다.

-----

## 🌟 1. Project Mission & Philosophy

  - **Context over Real-time**: 초단타 매매를 위한 틱(Tick) 데이터보다, \*\*"왜 올랐는가?"\*\*에 대한 맥락(Context)과 흐름을 저장합니다.
  - **Data Sovereignty (데이터 주권)**: 외부 뉴스 링크가 사라져도, 우리 DB에는 **AI가 추출한 핵심 요약과 팩트**가 영구 보존됩니다.
  - **Trustworthy AI**: AI의 환각(Hallucination)을 방지하기 위해 \*\*출처(Source Link)\*\*를 명시하고, 요약 과정에서 **교차 검증(Cross-Check)** 로직을 수행합니다.
  - **Scalable Horizon**: 초기 모델은 금융(Finance)에 집중하지만, 추후 밈(Meme), 제품 트렌드 등 **비정형 사회 트렌드 분석**으로 확장 가능한 유연한 스키마를 갖춥니다.

-----

## 🚀 2. Key Features

### A. Historical Trend (거시적 흐름 아카이빙)

  - **Time-Series Ranking**: 2015년부터 축적된 글로벌 시총 상위 기업의 순위 변동을 시각화합니다.
  - **Market Atmosphere**: 단순 등락률뿐만 아니라, 해당 시점의 시장을 지배했던 \*\*주요 키워드(Tag)\*\*와 \*\*감정 점수(Sentiment)\*\*를 함께 제공합니다.

### B. Daily AI Matchup (심층 비교 리포트)

  - **Deep Comparison**: 사용자가 두 기업(예: AAPL vs TSLA)을 선택하면, DB에 축적된 **과거 뉴스 히스토리**와 **재무 건전성**을 종합하여 승자를 판별합니다.
  - **Traceability**: AI의 분석 결과에는 반드시 **참고한 뉴스의 원문 링크**가 함께 제공되어, 사용자가 필요시 직접 검증할 수 있습니다.

### C. Insight Chatbot (Evidence-Based RAG)

  - "2023년 엔비디아 급등의 트리거는?"과 같은 질문에 대해, 학습된 일반 지식이 아닌 DB에 저장된 리포트 중 **검증이 완료된(`verified`) 데이터만**을 근거로 답변하여 정보의 정확도를 보장합니다.

-----

## 🛠️ 3. Tech Stack & Architecture

| 영역 | 주요 기술 | 역할 및 특징 |
| :--- | :--- | :--- |
| **Frontend** | React, Tailwind CSS | 데이터 시각화, 반응형 대시보드 |
| **Backend** | FastAPI | Python 3.11+, 비동기 처리, 의존성 주입(DI) 설계 |
| **Database** | PostgreSQL (Supabase) | `jsonb`를 활용한 Polymorphic Schema (주식/밈 데이터 통합) |
| **AI Engine** | OpenAI API (GPT-4o) | 데이터 요약, 감성 분석, **자가 검증(Self-Correction)** |
| **Data Ops** | **Snapshot & Pruning** | 원문 요약 저장 -\> 원문 본문 삭제 -\> 메타데이터(링크) 보존 |

### 🏗️ Data Pipeline: "Reliable Assetization"

우리는 **Snapshot & Pruning** 전략에 **Verification(검증)** 단계를 추가하여 데이터 신뢰도를 확보합니다.

```mermaid
graph LR
    A[External Sources] -->|Fetch Raw Text| B(Batch Collector)
    B -->|Raw Data| C{AI Processor}
    C -->|1. Summarize| D[Draft Summary]
    C -->|2. Verify| E{Logic Check}
    E -- Pass --> F[Save Summary & Link]
    E -- Fail --> G[Flag for Review]
    F -->|Pruning Body Text| H[(PostgreSQL)]
    H -->|Analysis Request| I[User Dashboard]
```

1.  **Collect**: `DuckDuckGo`, `yfinance` 등에서 일일 데이터 수집. (추후 `FMP` 등 유료 API로 교체 용이한 Interface 패턴 적용)
2.  **Process & Verify**:
      - AI가 뉴스 원문을 3줄 요약 및 감성 분석.
      - **검증 단계:** 요약문에 숫자가 포함된 경우, 원문과 일치하는지 가벼운 모델이 2차 확인.
3.  **Assetize (Pruning)**:
      - **저장:** 요약본, 감성 점수, **출처 URL**, 발행일자.
      - **삭제:** 용량을 차지하는 뉴스 본문 텍스트 (저작권 문제 해결 및 스토리지 최적화).

-----

## 📊 4. Database Schema Strategy

확장성과 검증 가능성을 고려한 스키마 설계입니다.

**`companies`**: 분석 대상 마스터 (Ticker, Name, **Category**)

> *Category: 'Stock', 'Crypto', 'Meme' 등으로 확장*

**`market_reports`**: 핵심 트렌드 데이터

  - `summary_content`: AI가 추출한 인사이트 (맥락)
  - `sentiment_score`: 시장 감정 (-1.0 \~ 1.0)
  - `source_url`: **원문 검증을 위한 링크 (Link Preservation)**
  - `verification_status`: AI 검증 통과 여부 (`verified`, `flagged`)

**`financials`**: 정량적 재무 데이터

-----

## ⚙️ 5. Roadmap

  - **v1.0 (MVP)**: 글로벌 주식 시총 상위 100개 기업 대상 일일 데이터 적재 및 분석.
  - **v1.1 (Stabilization)**: AI 요약 검증(Verification) 로직 고도화 및 데이터 파이프라인 안정화.
  - **v1.5 (Expansion)**: **Trend Expansion** - 주식 외 '소셜 밈(Meme)', '유행 제품' 등으로 분석 카테고리 확장.
  - **v2.0 (Premium)**: 무료 데이터 소스(`DuckDuckGo`)를 유료 API(`FMP`)로 교체하여 데이터 품질 격상.

-----

## 📦 6. Installation & Setup

### Backend (FastAPI)

```bash
# 1. Clone Repository
git clone https://github.com/space2532/Global-CapFlow.git
cd Global-CapFlow

# 2. Virtual Environment
python -m venv .venv 
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install Dependencies
pip install -r backend/requirements.txt

# 4. Environment Variables (.env)
# DATABASE_URL=postgresql://user:password@host:port/dbname
# OPENAI_API_KEY=sk-...

# 5. Run Server
uvicorn app.main:app --reload --app-dir backend
```