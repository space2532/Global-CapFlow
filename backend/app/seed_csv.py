"""
CSV 파일로부터 랭킹 및 기업 데이터를 DB에 적재하는 스크립트.
실행 방법: python -m app.seed_csv
"""
import asyncio
import csv
import os
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# 앱 설정 및 모델 임포트
from app.create_db import get_async_engine
from app import models

# ---------------------------------------------------------------------------
# 1. 회사 이름 -> 티커 매핑 (CSV에 티커가 없으므로 수동 매핑 필요)
# ---------------------------------------------------------------------------
NAME_TO_TICKER = {
    "Apple Inc.": "AAPL",
    "Microsoft Corp.": "MSFT",
    "Alphabet Inc.": "GOOGL",
    "Amazon.com, Inc.": "AMZN",
    "Nvidia Corp.": "NVDA",
    "Tesla, Inc.": "TSLA",
    "Meta Platforms, Inc.": "META",
    "Facebook, Inc.": "META",
    "Berkshire Hathaway Inc.": "BRK.B",
    "TSMC": "TSM",
    "Tencent Holdings Ltd.": "TCEHY",
    "Visa Inc.": "V",
    "UnitedHealth Group Inc.": "UNH",
    "Johnson & Johnson": "JNJ",
    "JPMorgan Chase & Co.": "JPM",
    "Eli Lilly and Co.": "LLY",
    "Broadcom Inc.": "AVGO",
    "Novo Nordisk A/S": "NVO",
    "Walmart Inc.": "WMT",
    "Exxon Mobil Corp.": "XOM",
    "Mastercard Inc.": "MA",
    "Samsung Electronics Co., Ltd.": "005930.KS",
    "Nestlé S.A.": "NSRGY",
    "Procter & Gamble Co.": "PG",
    "LVMH Moët Hennessy": "LVMUY",
    "LVMH": "LVMUY",
    "Roche Holding AG": "RHHBY",
    "ASML Holding N.V.": "ASML",
    "Chevron Corp.": "CVX",
    "Merck & Co., Inc.": "MRK",
    "Home Depot, Inc.": "HD",
    "Toyota Motor Corp.": "TM",
    "Alibaba Group Holding Ltd.": "BABA",
    "Saudi Aramco": "ARAMCO",
    "Bank of America Corp.": "BAC",
    "ICBC": "IDCBY",
    "General Electric Co.": "GE",
    "Wells Fargo & Co.": "WFC",
    "China Mobile Ltd.": "0941.HK",
    "AT&T Inc.": "T",
    "Costco Wholesale Corp.": "COST",
    "PepsiCo, Inc.": "PEP",
    "Coca-Cola Co.": "KO",
    "AbbVie Inc.": "ABBV",
    "Oracle Corp.": "ORCL",
    "Adobe Inc.": "ADBE",
    "Netflix Inc.": "NFLX",
    "Salesforce.com Inc": "CRM",
    "Salesforce, Inc.": "CRM",
    "Pfizer Inc.": "PFE",
    "Thermo Fisher Scientific Inc.": "TMO",
    "Abbott Laboratories": "ABT",
    "Cisco Systems, Inc.": "CSCO",
    "McDonald's Corp.": "MCD",
    "Accenture plc": "ACN",
    "Linde plc": "LIN",
    "Shell plc": "SHEL",
    "AstraZeneca plc": "AZN",
    "Novartis AG": "NVS",
    "Hermès International": "HESAY",
    "SAP SE": "SAP",
    "AMD": "AMD",
    "Qualcomm Inc.": "QCOM",
    "Intuit Inc.": "INTU",
    "Intel Corp.": "INTC",
    "Comcast Corp.": "CMCSA",
    "Verizon Communications Inc.": "VZ",
    "Walt Disney Co.": "DIS",
    "Nike, Inc.": "NKE",
    "Danaher Corp.": "DHR",
    "Texas Instruments Inc.": "TXN",
    "Union Pacific Corp.": "UNP",
    "Honeywell International Inc.": "HON",
    "Boeing Co.": "BA",
    "Caterpillar Inc.": "CAT",
    "3M Company": "MMM",
    "Lockheed Martin Corp.": "LMT",
    "American Express Co.": "AXP",
    "Goldman Sachs Group, Inc.": "GS",
    "Morgan Stanley": "MS",
    "BlackRock, Inc.": "BLK",
    "Charles Schwab Corp.": "SCHW",
    "Starbucks Corp.": "SBUX",
    "Bristol-Myers Squibb Co.": "BMY",
    "CVS Health Corp.": "CVS",
    "Siemens AG": "SIEGY",
    "Sony Group Corp.": "SONY",
    "SoftBank Group Corp.": "SFTBY",
    "BYD Company Ltd.": "BYDDY",
    "Meituan": "MPNGY",
    "Pinduoduo Inc.": "PDD",
    "PDD Holdings Inc.": "PDD",
    "China Construction Bank Corp.": "CICHY",
    "Hyundai Motor Co.": "HYMTF",
    "SK Hynix Inc.": "HXSCF",
    "POSCO Holdings Inc.": "PKX",
    "Naver Corp.": "035420.KS",
    "Kakao Corp.": "035720.KS",
    "Rio Tinto plc": "RIO",
    "BHP Group": "BHP",
    "Airbus SE": "EADSY",
    "Ferrari N.V.": "RACE",
    "TotalEnergies SE": "TTE",
    "IBM": "IBM",
    "Uber Technologies, Inc.": "UBER"
}

# CSV 파일 목록
CSV_FILES = {
    2015: "market_cap_2015.csv",
    2016: "market_cap_2016.csv",
    2017: "market_cap_2017.csv",
    2018: "market_cap_2018.csv",
    2019: "market_cap_2019.csv",
    2020: "market_cap_2020.csv",
    2021: "market_cap_2021.csv",
    2022: "market_cap_2022.csv",
    2023: "market_cap_2023.csv",
    2024: "market_cap_2024.csv",
}

# ✅ 데이터 폴더 경로 설정 (현재 작업 디렉토리 기준 'data' 폴더)
DATA_DIR = os.path.join(os.getcwd(), "data")

async def seed_year(session: AsyncSession, year: int, filename: str):
    """특정 연도의 CSV 파일을 읽어 DB에 적재"""
    
    # ✅ 경로 수정: DATA_DIR 사용
    filepath = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️  [Year {year}] File not found: {filepath}")
        return

    print(f"📂 [Year {year}] Processing {filename}...")
    
    count = 0
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rank = int(row.get("rank"))
                name = row.get("company_name", "").strip()
                market_cap_usd = float(row.get("market_cap_usd", 0))
                logo_url = row.get("logo_url", "")
                
                # 티커 매핑 확인
                ticker = NAME_TO_TICKER.get(name)
                if not ticker:
                    continue

                # 1. Company 존재 확인 및 생성
                stmt_company = select(models.Company).where(models.Company.ticker == ticker)
                result = await session.execute(stmt_company)
                company = result.scalar_one_or_none()

                if not company:
                    company = models.Company(
                        ticker=ticker,
                        name=name,
                        logo_url=logo_url,
                        category="Stock"
                    )
                    session.add(company)
                    await session.flush()

                # 2. Ranking 데이터 Upsert
                stmt_ranking = select(models.Ranking).where(
                    models.Ranking.year == year,
                    models.Ranking.ticker == ticker
                )
                result = await session.execute(stmt_ranking)
                existing_ranking = result.scalar_one_or_none()

                if existing_ranking:
                    existing_ranking.rank = rank
                    existing_ranking.market_cap = market_cap_usd
                    existing_ranking.company_name = name
                else:
                    new_ranking = models.Ranking(
                        year=year,
                        rank=rank,
                        ticker=ticker,
                        market_cap=market_cap_usd,
                        company_name=name
                    )
                    session.add(new_ranking)
                
                count += 1

            except Exception as e:
                print(f"❌ Error processing row {row}: {e}")

    await session.commit()
    print(f"✅ [Year {year}] Completed. {count} records processed.")


async def main():
    # 데이터 폴더 확인
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory not found at {DATA_DIR}")
        print("Please create a 'data' folder in the backend directory and move CSV files there.")
        return

    engine = get_async_engine()
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        for year, filename in CSV_FILES.items():
            await seed_year(session, year, filename)

    await engine.dispose()
    print("\n🎉 All CSV data seeding completed!")

if __name__ == "__main__":
    asyncio.run(main())