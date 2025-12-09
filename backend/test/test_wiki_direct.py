"""
위키피디아 직접 테스트
"""

import pandas as pd
import sys

urls = [
    "https://en.wikipedia.org/wiki/S%26P_500_Index",
    "https://en.wikipedia.org/wiki/NASDAQ-100",
]

print("Testing pandas.read_html with Wikipedia URLs...\n")

for url in urls:
    print(f"Testing: {url}")
    try:
        # 여러 파서 시도
        tables = None
        parser = None
        
        for parser_name in ['html5lib', 'lxml', None]:
            try:
                if parser_name:
                    tables = pd.read_html(url, flavor=parser_name)
                    parser = parser_name
                    break
                else:
                    tables = pd.read_html(url)
                    parser = 'default'
                    break
            except Exception as e:
                print(f"  {parser_name or 'default'} 파서 실패: {str(e)[:100]}")
                continue
        
        if tables:
            print(f"  ✅ 성공! ({parser} 파서, {len(tables)}개 테이블)")
            
            # 첫 번째 테이블의 컬럼 확인
            if len(tables) > 0:
                print(f"  첫 번째 테이블 컬럼: {list(tables[0].columns)[:10]}")
                
                # Symbol 컬럼 찾기
                for col in ["Symbol", "Ticker", "Ticker symbol", "Symbols", "Code"]:
                    if col in tables[0].columns:
                        print(f"  ✅ '{col}' 컬럼 발견!")
                        print(f"  샘플 티커: {list(tables[0][col].dropna().head(5))}")
                        break
        else:
            print(f"  ❌ 모든 파서 실패!")
            
    except Exception as e:
        print(f"  ❌ 오류: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        print(f"  상세: {traceback.format_exc()[:300]}")
    
    print()


