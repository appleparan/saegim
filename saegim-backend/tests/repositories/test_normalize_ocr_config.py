"""Tests for normalize_ocr_config in project_repo."""

from saegim.repositories.project_repo import normalize_ocr_config


class TestNormalizeOcrConfig:
    def test_empty_dict(self):
        result = normalize_ocr_config({})
        assert result == {'default_engine_id': None, 'engines': {}}

    def test_already_new_format_passthrough(self):
        new_format = {
            'default_engine_id': 'my-engine',
            'engines': {
                'my-engine': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
            },
        }
        result = normalize_ocr_config(new_format)
        assert result is new_format

    def test_old_pdfminer_only(self):
        result = normalize_ocr_config({'engine_type': 'pdfminer'})
        assert result['default_engine_id'] is None
        assert result['engines'] == {}

    def test_old_commercial_api(self):
        old = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        }
        result = normalize_ocr_config(old)
        assert result['default_engine_id'] == 'commercial-api'
        assert 'commercial-api' in result['engines']
        engine = result['engines']['commercial-api']
        assert engine['engine_type'] == 'commercial_api'
        assert engine['name'] == 'Gemini API'
        assert engine['config']['api_key'] == 'test-key'

    def test_old_vllm(self):
        old = {
            'engine_type': 'vllm',
            'vllm': {
                'host': 'gpu-server',
                'port': 8000,
                'model': 'datalab-to/chandra',
            },
        }
        result = normalize_ocr_config(old)
        assert result['default_engine_id'] == 'vllm'
        assert 'vllm' in result['engines']
        assert result['engines']['vllm']['engine_type'] == 'vllm'
        assert result['engines']['vllm']['name'] == 'vLLM'

    def test_old_split_pipeline(self):
        old = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'docling_model_name': 'ibm-granite/granite-docling-258M',
                'ocr_provider': 'gemini',
                'ocr_api_key': 'key',
            },
        }
        result = normalize_ocr_config(old)
        assert result['default_engine_id'] == 'split-pipeline'
        assert 'split-pipeline' in result['engines']
        assert result['engines']['split-pipeline']['engine_type'] == 'split_pipeline'

    def test_old_multiple_sub_configs(self):
        old = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'key',
                'model': 'gemini-3-flash-preview',
            },
            'vllm': {
                'host': 'localhost',
                'port': 8000,
                'model': 'datalab-to/chandra',
            },
            'enabled_engines': ['commercial_api', 'vllm'],
        }
        result = normalize_ocr_config(old)
        assert result['default_engine_id'] == 'commercial-api'
        assert len(result['engines']) == 2
        assert 'commercial-api' in result['engines']
        assert 'vllm' in result['engines']

    def test_old_pdfminer_with_sub_configs(self):
        old = {
            'engine_type': 'pdfminer',
            'vllm': {
                'host': 'localhost',
                'port': 8000,
            },
        }
        result = normalize_ocr_config(old)
        assert result['default_engine_id'] is None
        assert 'vllm' in result['engines']

    def test_no_engine_type_key(self):
        result = normalize_ocr_config({'some_old_key': 'value'})
        assert result == {'default_engine_id': None, 'engines': {}}

    def test_preserves_config_data(self):
        old = {
            'engine_type': 'vllm',
            'vllm': {
                'host': 'custom-host',
                'port': 9999,
                'model': 'custom-model',
            },
        }
        result = normalize_ocr_config(old)
        config = result['engines']['vllm']['config']
        assert config['host'] == 'custom-host'
        assert config['port'] == 9999
        assert config['model'] == 'custom-model'
