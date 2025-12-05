# Matchup API 테스트 가이드

## 🚀 빠른 시작

### 1. 서버 실행

```bash
# backend 디렉토리에서 실행
cd backend
uvicorn app.main:app --reload --app-dir .
```

또는 프로젝트 루트에서:

```bash
uvicorn app.main:app --reload --app-dir backend
```

서버가 실행되면 `http://localhost:8000`에서 접근 가능합니다.

---

## 📋 테스트 방법

### 방법 1: Swagger UI (가장 쉬움) ⭐

1. 브라우저에서 `http://localhost:8000/docs` 접속
2. `/analyze/matchup` 엔드포인트 찾기
3. "Try it out" 클릭
4. Request body 입력:
   ```json
   {
     "tickers": ["AAPL", "TSLA"],
     "query": "성장성 관점에서 비교해줘"
   }
   ```
5. "Execute" 클릭
6. 결과 확인

**장점**: 
- 별도 도구 불필요
- API 스키마 자동 문서화
- 인터랙티브 테스트

---

### 방법 2: Python 테스트 스크립트

```bash
# 프로젝트 루트에서 실행
python backend/test_matchup_api.py
```

이 스크립트는 다음을 테스트합니다:
- ✅ Health check
- ✅ 기본 Matchup API 호출
- ✅ 질문 포함 Matchup API 호출
- ✅ 캐싱 동작 확인

---

### 방법 3: curl 명령어

#### 기본 요청 (질문 없음)
```bash
curl -X POST "http://localhost:8000/analyze/matchup" \
     -H "Content-Type: application/json" \
     -d '{
       "tickers": ["AAPL", "TSLA"]
     }'
```

#### 질문 포함 요청
```bash
curl -X POST "http://localhost:8000/analyze/matchup" \
     -H "Content-Type: application/json" \
     -d '{
       "tickers": ["AAPL", "TSLA"],
       "query": "성장성 관점에서 비교해줘"
     }'
```

#### 예쁘게 출력 (jq 사용)
```bash
curl -X POST "http://localhost:8000/analyze/matchup" \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["AAPL", "TSLA"]}' \
     | jq .
```

---

### 방법 4: Python requests

```python
import requests
import json

url = "http://localhost:8000/analyze/matchup"
payload = {
    "tickers": ["AAPL", "TSLA"],
    "query": "성장성 관점에서 비교해줘"  # 선택사항
}

response = requests.post(url, json=payload, timeout=120)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

---

### 방법 5: Postman / Insomnia

1. **Method**: POST
2. **URL**: `http://localhost:8000/analyze/matchup`
3. **Headers**: 
   - `Content-Type: application/json`
4. **Body** (JSON):
   ```json
   {
     "tickers": ["AAPL", "TSLA"],
     "query": "성장성 관점에서 비교해줘"
   }
   ```

---

## 📝 요청 예시

### 예시 1: 두 기업 비교
```json
{
  "tickers": ["AAPL", "TSLA"]
}
```

### 예시 2: 세 기업 비교
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

### 예시 3: 질문 포함
```json
{
  "tickers": ["AAPL", "TSLA"],
  "query": "수익성 관점에서 어떤 기업이 더 유리한가?"
}
```

---

## 📤 응답 예시

```json
{
  "winner": "AAPL",
  "reason": "AAPL은 안정적인 수익성과 강력한 브랜드 파워를 보유하고 있으며, TSLA는 높은 성장 잠재력이 있지만 변동성이 큽니다.",
  "summary": "AAPL과 TSLA를 비교한 결과, AAPL이 전반적인 안정성과 수익성 측면에서 우위를 보입니다. TSLA는 전기차 시장의 성장 잠재력이 크지만, 변동성과 경쟁 심화로 인한 리스크가 존재합니다.",
  "key_comparison": [
    {
      "metric": "매출",
      "winner": "AAPL",
      "reason": "AAPL의 매출이 TSLA보다 훨씬 높습니다."
    },
    {
      "metric": "성장성",
      "winner": "TSLA",
      "reason": "TSLA의 성장률이 더 높습니다."
    },
    {
      "metric": "PER",
      "winner": "AAPL",
      "reason": "AAPL의 PER이 더 합리적입니다."
    }
  ]
}
```

---

## ⚠️ 주의사항

1. **첫 요청은 시간이 걸립니다**
   - 데이터 수집 (yfinance, DuckDuckGo)
   - AI 분석 (OpenAI API)
   - 예상 소요 시간: 30초 ~ 2분

2. **캐싱 동작**
   - 동일한 티커 조합은 24시간 이내 캐시 사용
   - 티커 순서는 상관없음 (예: ["AAPL", "TSLA"] = ["TSLA", "AAPL"])

3. **에러 처리**
   - 최소 2개 이상의 티커 필요
   - 티커는 자동으로 대문자 변환
   - 일부 티커 데이터 수집 실패해도 다른 티커 분석 계속 진행

---

## 🔍 디버깅

### 서버 로그 확인
서버 실행 시 터미널에서 다음 로그를 확인할 수 있습니다:
```
➡️ [AnalyzeRouter] Matchup analysis requested for ['AAPL', 'TSLA']
📊 [AnalyzeRouter] Fetching data for ['AAPL', 'TSLA']...
🧠 [AnalyzeRouter] Running AI matchup analysis...
✅ [AnalyzeRouter] Analysis result cached
```

### Health Check
```bash
curl http://localhost:8000/health
```

### API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 문제 해결

### "Connection refused" 오류
→ 서버가 실행 중인지 확인하세요.

### "Timeout" 오류
→ AI 분석이 오래 걸릴 수 있습니다. 타임아웃을 늘리거나 잠시 후 재시도하세요.

### "OpenAI API 키가 설정되지 않았습니다"
→ `.env` 파일에 `OPENAI_API_KEY`를 설정하세요.

### "최소 2개 이상의 티커가 필요합니다"
→ `tickers` 배열에 최소 2개의 티커를 포함하세요.
