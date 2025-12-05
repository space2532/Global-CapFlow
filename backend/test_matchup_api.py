"""
Matchup API 테스트 스크립트

사용법:
1. FastAPI 서버가 실행 중이어야 합니다:
   uvicorn app.main:app --reload --app-dir backend

2. 이 스크립트를 실행:
   python backend/test_matchup_api.py
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def test_health_check():
    """서버 상태 확인"""
    print("\n" + "="*50)
    print("1. Health Check 테스트")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_matchup_api(tickers: list[str], query: str | None = None):
    """Matchup API 테스트"""
    print("\n" + "="*50)
    print(f"2. Matchup API 테스트 - 티커: {tickers}")
    if query:
        print(f"   질문: {query}")
    print("="*50)
    
    payload: Dict[str, Any] = {
        "tickers": tickers
    }
    if query:
        payload["query"] = query
    
    print(f"\n요청 URL: {BASE_URL}/analyze/matchup")
    print(f"요청 Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        print("\n⏳ API 호출 중... (처음 호출은 데이터 수집 및 AI 분석으로 인해 시간이 걸릴 수 있습니다)")
        response = requests.post(
            f"{BASE_URL}/analyze/matchup",
            json=payload,
            timeout=120  # 2분 타임아웃 (AI 분석 시간 고려)
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 성공!")
            print("\n응답 결과:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 결과 요약
            print("\n" + "-"*50)
            print("📊 분석 결과 요약:")
            print(f"   승자: {result.get('winner', 'N/A')}")
            print(f"   요약: {result.get('summary', 'N/A')[:100]}...")
            print(f"   비교 포인트 수: {len(result.get('key_comparison', []))}")
            print("-"*50)
            
            return True
        else:
            print(f"\n❌ 실패!")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ 타임아웃 발생 (120초 초과)")
        print("   AI 분석이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ 연결 실패")
        print("   FastAPI 서버가 실행 중인지 확인하세요:")
        print("   uvicorn app.main:app --reload --app-dir backend")
        return False
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return False


def test_matchup_caching(tickers: list[str]):
    """캐싱 테스트 (동일한 요청을 두 번 보내서 두 번째는 캐시 사용)"""
    print("\n" + "="*50)
    print("3. 캐싱 테스트")
    print("="*50)
    
    payload = {"tickers": tickers}
    
    print("\n첫 번째 요청 (캐시 없음, AI 분석 수행)...")
    import time
    start1 = time.time()
    response1 = requests.post(
        f"{BASE_URL}/analyze/matchup",
        json=payload,
        timeout=120
    )
    time1 = time.time() - start1
    
    if response1.status_code != 200:
        print("❌ 첫 번째 요청 실패")
        return False
    
    print(f"✅ 첫 번째 요청 완료 (소요 시간: {time1:.2f}초)")
    
    print("\n두 번째 요청 (캐시 사용 예상)...")
    start2 = time.time()
    response2 = requests.post(
        f"{BASE_URL}/analyze/matchup",
        json=payload,
        timeout=120
    )
    time2 = time.time() - start2
    
    if response2.status_code != 200:
        print("❌ 두 번째 요청 실패")
        return False
    
    print(f"✅ 두 번째 요청 완료 (소요 시간: {time2:.2f}초)")
    
    if time2 < time1 * 0.5:  # 두 번째가 훨씬 빠르면 캐시 사용 가능성
        print(f"\n✅ 캐싱이 작동하는 것으로 보입니다!")
        print(f"   첫 번째: {time1:.2f}초")
        print(f"   두 번째: {time2:.2f}초 ({time1/time2:.1f}x 빠름)")
    else:
        print(f"\n⚠️ 캐싱이 작동하지 않거나 차이가 크지 않습니다.")
        print(f"   첫 번째: {time1:.2f}초")
        print(f"   두 번째: {time2:.2f}초")
    
    return True


def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🚀 Matchup API 테스트 시작")
    print("="*60)
    
    # 1. Health Check
    if not test_health_check():
        print("\n❌ 서버가 실행 중이지 않습니다. 서버를 먼저 시작하세요.")
        return
    
    # 2. 기본 Matchup 테스트
    print("\n\n" + "="*60)
    print("📊 기본 Matchup 테스트 (AAPL vs TSLA)")
    print("="*60)
    test_matchup_api(["AAPL", "TSLA"])
    
    # 3. 질문이 포함된 Matchup 테스트
    print("\n\n" + "="*60)
    print("📊 질문 포함 Matchup 테스트 (MSFT vs GOOGL)")
    print("="*60)
    test_matchup_api(
        ["MSFT", "GOOGL"],
        query="성장성 관점에서 비교해줘"
    )
    
    # 4. 캐싱 테스트
    print("\n\n" + "="*60)
    print("💾 캐싱 테스트")
    print("="*60)
    test_matchup_caching(["AAPL", "TSLA"])
    
    print("\n\n" + "="*60)
    print("✅ 모든 테스트 완료!")
    print("="*60)
    print("\n💡 추가 테스트 방법:")
    print("   1. Swagger UI: http://localhost:8000/docs")
    print("   2. ReDoc: http://localhost:8000/redoc")
    print("   3. curl 명령어:")
    print('      curl -X POST "http://localhost:8000/analyze/matchup" \\')
    print('           -H "Content-Type: application/json" \\')
    print('           -d \'{"tickers": ["AAPL", "TSLA"]}\'')


if __name__ == "__main__":
    main()
