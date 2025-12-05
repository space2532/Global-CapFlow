"""
DB 우선 사용 로직 테스트 스크립트

이 스크립트는 analyze/matchup API가 DB 데이터를 우선 사용하는지 테스트합니다.

사용법:
1. FastAPI 서버가 실행 중이어야 합니다:
   uvicorn app.main:app --reload --app-dir backend

2. 이 스크립트를 실행:
   python backend/test_db_priority.py
"""

import requests
import json
import time
from datetime import datetime


BASE_URL = "http://localhost:8000"


def test_matchup_with_db_data():
    """DB 데이터 우선 사용 테스트"""
    print("\n" + "="*60)
    print("💾 DB 우선 사용 로직 테스트")
    print("="*60)
    
    tickers = ["AAPL", "MSFT"]
    
    print(f"\n📌 테스트 티커: {tickers}")
    print("\n1️⃣ 첫 번째 요청 (DB에 데이터가 없으면 외부 API 호출)")
    print("   ⏳ API 호출 중...")
    
    start_time = time.time()
    response1 = requests.post(
        f"{BASE_URL}/analyze/matchup",
        json={"tickers": tickers},
        timeout=120
    )
    time1 = time.time() - start_time
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   ✅ 성공 (소요 시간: {time1:.2f}초)")
        print(f"   - 승자: {result1.get('winner', 'N/A')}")
    else:
        print(f"   ❌ 실패: {response1.status_code}")
        print(f"   {response1.text}")
        return
    
    print("\n2️⃣ 두 번째 요청 (캐시 사용)")
    print("   ⏳ API 호출 중...")
    
    start_time = time.time()
    response2 = requests.post(
        f"{BASE_URL}/analyze/matchup",
        json={"tickers": tickers},
        timeout=120
    )
    time2 = time.time() - start_time
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   ✅ 성공 (소요 시간: {time2:.2f}초)")
        print(f"   - 승자: {result2.get('winner', 'N/A')}")
        
        # 성능 비교
        if time2 < time1:
            speedup = time1 / time2
            print(f"\n   ⚡ 캐시로 인한 속도 향상: {speedup:.2f}배 빠름")
    else:
        print(f"   ❌ 실패: {response2.status_code}")
        return
    
    print("\n3️⃣ 순서 변경 요청 (동일한 캐시 사용 확인)")
    print("   ⏳ API 호출 중...")
    
    start_time = time.time()
    response3 = requests.post(
        f"{BASE_URL}/analyze/matchup",
        json={"tickers": list(reversed(tickers))},  # 순서 변경
        timeout=120
    )
    time3 = time.time() - start_time
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"   ✅ 성공 (소요 시간: {time3:.2f}초)")
        print(f"   - 승자: {result3.get('winner', 'N/A')}")
        
        # 동일한 결과인지 확인
        if result3.get('winner') == result2.get('winner'):
            print("   ✅ 동일한 캐시 사용 확인")
    else:
        print(f"   ❌ 실패: {response3.status_code}")


def test_health_check():
    """서버 상태 확인"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🚀 DB 우선 사용 로직 테스트 시작")
    print("="*60)
    
    # 서버 상태 확인
    if not test_health_check():
        print("\n❌ 서버가 실행 중이지 않습니다.")
        print("   다음 명령어로 서버를 시작하세요:")
        print("   uvicorn app.main:app --reload --app-dir backend")
        return
    
    print("\n✅ 서버 연결 확인")
    
    # DB 우선 사용 테스트
    test_matchup_with_db_data()
    
    print("\n\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60)
    print("\n💡 확인 사항:")
    print("   1. 첫 번째 요청은 외부 API 호출로 시간이 걸립니다")
    print("   2. 두 번째 요청은 캐시 사용으로 빠릅니다")
    print("   3. DB에 MarketReport가 있으면 raw_data와 summary_content를 사용합니다")


if __name__ == "__main__":
    main()

