-- Supabase SQL Editor에서 실행할 마이그레이션 스크립트
-- companies 테이블에 logo_url 필드 추가 (FMP API 로고 URL 저장용)

-- companies 테이블에 logo_url 필드 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'logo_url'
    ) THEN
        ALTER TABLE companies 
        ADD COLUMN logo_url VARCHAR(512);
    END IF;
END $$;

-- 완료 메시지
SELECT 'Migration completed successfully! logo_url column added to companies table.' AS status;





