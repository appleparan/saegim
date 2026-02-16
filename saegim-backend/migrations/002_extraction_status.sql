-- Add extracting and extraction_failed to documents status
-- Required for async MinerU extraction via Celery

ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_status_check;
ALTER TABLE documents ADD CONSTRAINT documents_status_check
    CHECK (status IN ('uploading', 'processing', 'extracting', 'ready', 'error', 'extraction_failed'));
