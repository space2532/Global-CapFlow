-- Supabase SQL Editor에서 실행할 마이그레이션 스크립트
-- 기존 데이터가 있어도 에러가 나지 않도록 IF NOT EXISTS 로직 사용

-- 1. Company 테이블에 category 필드 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'category'
    ) THEN
        ALTER TABLE companies 
        ADD COLUMN category VARCHAR(32) DEFAULT 'Stock';
        
        -- 기존 데이터에 기본값 설정
        UPDATE companies SET category = 'Stock' WHERE category IS NULL;
    END IF;
END $$;

-- 2. MarketReport 테이블에 summary_content 필드 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'market_reports' AND column_name = 'summary_content'
    ) THEN
        ALTER TABLE market_reports 
        ADD COLUMN summary_content TEXT;
    END IF;
END $$;

-- 3. MarketReport 테이블에 sentiment_score 필드 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'market_reports' AND column_name = 'sentiment_score'
    ) THEN
        ALTER TABLE market_reports 
        ADD COLUMN sentiment_score DOUBLE PRECISION;
    END IF;
    
    -- CHECK 제약조건 추가: -1.0 ~ 1.0 범위 (제약조건이 없을 경우에만)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'market_reports' 
        AND constraint_name = 'chk_sentiment_score_range'
    ) THEN
        ALTER TABLE market_reports 
        ADD CONSTRAINT chk_sentiment_score_range 
        CHECK (sentiment_score IS NULL OR (sentiment_score >= -1.0 AND sentiment_score <= 1.0));
    END IF;
END $$;

-- 4. MarketReport 테이블에 raw_data 필드 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'market_reports' AND column_name = 'raw_data'
    ) THEN
        ALTER TABLE market_reports 
        ADD COLUMN raw_data TEXT;
    END IF;
END $$;

-- 5. 기존 content 필드를 nullable로 변경 (하위 호환성 유지)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'market_reports' 
        AND column_name = 'content' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE market_reports 
        ALTER COLUMN content DROP NOT NULL;
    END IF;
END $$;

-- 완료 메시지
SELECT 'Migration completed successfully!' AS status;

-- 6. financials 테이블에 quarter 컬럼 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'financials' AND column_name = 'quarter'
    ) THEN
        ALTER TABLE financials
        ADD COLUMN quarter INTEGER;
    END IF;
END $$;

-- 7. 기존 유니크 제약 (ticker, year) 제거
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'financials'
          AND constraint_name = 'uq_financials_ticker_year'
    ) THEN
        ALTER TABLE financials
        DROP CONSTRAINT uq_financials_ticker_year;
    END IF;
END $$;

-- 8. 새 유니크 제약 (ticker, year, quarter) 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'financials'
          AND constraint_name = 'uq_financials_ticker_year_quarter'
    ) THEN
        ALTER TABLE financials
        ADD CONSTRAINT uq_financials_ticker_year_quarter
        UNIQUE (ticker, year, quarter);
    END IF;
END $$;

-- 9. financials.quarter 값 범위 제한 (0 또는 1~4 허용)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'financials'
          AND constraint_name = 'chk_financials_quarter_range'
    ) THEN
        ALTER TABLE financials
        ADD CONSTRAINT chk_financials_quarter_range
        CHECK (quarter IS NULL OR quarter BETWEEN 0 AND 4);
    END IF;
END $$;

-- 10. prices 테이블 생성 (월별 주가)
CREATE TABLE IF NOT EXISTS prices (
    id          bigserial PRIMARY KEY,
    ticker      text NOT NULL REFERENCES companies (ticker) ON DELETE CASCADE,
    "date"      timestamptz NOT NULL,
    close       double precision,
    market_cap  double precision,
    volume      bigint,
    CONSTRAINT uq_prices_ticker_date UNIQUE (ticker, "date")
);

CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
    ON prices (ticker, "date");

CREATE INDEX IF NOT EXISTS idx_prices_date
    ON prices ("date");

-- 11. rankings 테이블 생성 (연도별 시가총액 순위)
CREATE TABLE IF NOT EXISTS rankings (
    id           bigserial PRIMARY KEY,
    year         integer NOT NULL,
    rank         integer NOT NULL,
    ticker       text NOT NULL REFERENCES companies (ticker) ON DELETE CASCADE,
    market_cap   double precision,
    company_name text NOT NULL,
    CONSTRAINT uq_rankings_year_rank UNIQUE (year, rank)
);

CREATE INDEX IF NOT EXISTS idx_rankings_year
    ON rankings (year);

CREATE INDEX IF NOT EXISTS idx_rankings_ticker_year
    ON rankings (ticker, year);

-- 12. companies.category 값 제한 CHECK 제약 (선택적으로 수정 가능)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'companies'
          AND constraint_name = 'chk_companies_category'
    ) THEN
        ALTER TABLE companies
        ADD CONSTRAINT chk_companies_category
        CHECK (category IN ('Stock', 'Meme', 'Product'));
    END IF;
END $$;

-- 13. rankings 테이블에 ranking_date 컬럼 추가 (월별 관리용)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'rankings' AND column_name = 'ranking_date'
    ) THEN
        ALTER TABLE rankings
        ADD COLUMN ranking_date date;
    END IF;
END $$;

-- 14. rankings 유니크 제약을 (year, rank) → (ranking_date, rank)로 변경
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'rankings'
          AND constraint_name = 'uq_rankings_year_rank'
    ) THEN
        ALTER TABLE rankings
        DROP CONSTRAINT uq_rankings_year_rank;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'rankings'
          AND constraint_name = 'uq_rankings_ranking_date_rank'
    ) THEN
        ALTER TABLE rankings
        ADD CONSTRAINT uq_rankings_ranking_date_rank
        UNIQUE (ranking_date, rank);
    END IF;
END $$;

-- 15. rankings.ranking_date 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_rankings_ranking_date
    ON rankings (ranking_date);

-- 16. sector_trends 테이블 생성 (월별 산업 트렌드)
CREATE TABLE IF NOT EXISTS sector_trends (
    id               bigserial PRIMARY KEY,
    "date"           date NOT NULL,
    dominant_sectors jsonb,
    rising_sectors   jsonb,
    new_entries      jsonb,
    ai_analysis_text text,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sector_trends_date
    ON sector_trends ("date");

-- 17. quarterly_reports 테이블 생성 (분기별 기업 분석 보고서)
CREATE TABLE IF NOT EXISTS quarterly_reports (
    id          bigserial PRIMARY KEY,
    ticker      text NOT NULL REFERENCES companies (ticker) ON DELETE CASCADE,
    "year"      integer NOT NULL,
    quarter     integer NOT NULL,
    content     text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_quarterly_reports_ticker_year_quarter UNIQUE (ticker, "year", quarter)
);

CREATE INDEX IF NOT EXISTS idx_quarterly_reports_ticker_year_quarter
    ON quarterly_reports (ticker, "year", quarter);