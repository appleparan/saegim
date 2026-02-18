-- Add ocr_config JSONB column to projects table
-- Stores per-project OCR provider configuration
--
-- ocr_config structure:
-- {
--   "provider": "gemini" | "vllm" | "mineru" | "pymupdf",
--   "gemini": { "api_key": "...", "model": "gemini-2.0-flash" },
--   "vllm": { "host": "localhost", "port": 8000, "model": "Qwen/Qwen2.5-VL-72B-Instruct" }
-- }

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS ocr_config JSONB DEFAULT NULL;

COMMENT ON COLUMN projects.ocr_config IS 'Per-project OCR provider configuration (provider, API keys, host/port)';
