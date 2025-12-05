-- collected_at 컬럼을 TIMESTAMP WITH TIME ZONE으로 변경하는 마이그레이션
-- Supabase SQL Editor에서 실행

-- 1. collected_at 컬럼 타입 확인 및 변경
DO $$
BEGIN
    -- 현재 타입 확인
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'market_reports'
          AND column_name = 'collected_at'
          AND data_type = 'timestamp without time zone'
    ) THEN
        -- TIMESTAMP WITHOUT TIME ZONE을 TIMESTAMP WITH TIME ZONE으로 변경
        ALTER TABLE market_reports
        ALTER COLUMN collected_at TYPE TIMESTAMP WITH TIME ZONE
        USING collected_at AT TIME ZONE 'UTC';
        
        RAISE NOTICE 'collected_at 컬럼이 TIMESTAMP WITH TIME ZONE으로 변경되었습니다.';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'market_reports'
          AND column_name = 'collected_at'
          AND data_type = 'timestamp with time zone'
    ) THEN
        RAISE NOTICE 'collected_at 컬럼이 이미 TIMESTAMP WITH TIME ZONE입니다.';
    ELSE
        RAISE NOTICE 'collected_at 컬럼을 찾을 수 없습니다.';
    END IF;
END $$;

-- 완료 메시지
SELECT 'Migration completed successfully!' AS status;
