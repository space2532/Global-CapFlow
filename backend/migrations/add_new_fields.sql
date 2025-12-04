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

