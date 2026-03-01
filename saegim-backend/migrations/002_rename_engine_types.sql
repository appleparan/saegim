-- Migrate OCR engine type names after refactoring
-- integrated_server → vllm, docling → pdfminer (fallback)
-- split_pipeline: layout_server_url → docling_model_name

-- 1. Rename integrated_server → vllm
UPDATE projects
SET ocr_config = jsonb_set(
    ocr_config, '{engine_type}', '"vllm"'
) || jsonb_build_object('vllm', ocr_config->'integrated_server')
   - 'integrated_server'
WHERE ocr_config->>'engine_type' = 'integrated_server';

-- 2. Downgrade standalone docling → pdfminer (fallback)
UPDATE projects
SET ocr_config = '{"engine_type": "pdfminer"}'::jsonb
WHERE ocr_config->>'engine_type' = 'docling';

-- 3. split_pipeline: replace layout_server_url with docling_model_name
UPDATE projects
SET ocr_config = jsonb_set(
    ocr_config, '{split_pipeline}',
    (ocr_config->'split_pipeline') - 'layout_server_url'
    || '{"docling_model_name": "ibm-granite/granite-docling-258M"}'::jsonb
)
WHERE ocr_config->>'engine_type' = 'split_pipeline'
  AND ocr_config->'split_pipeline' IS NOT NULL;
