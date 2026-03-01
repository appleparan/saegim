"""Tests for engine factory."""

from unittest.mock import patch

import pytest

from saegim.services.engines.factory import build_engine

_MODULE = 'saegim.services.engines.factory'


class TestBuildEngine:
    def test_pdfminer_engine(self):
        engine = build_engine({'engine_type': 'pdfminer'})
        from saegim.services.engines.pdfminer_engine import PdfminerEngine

        assert isinstance(engine, PdfminerEngine)

    def test_commercial_api_gemini(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        }
        engine = build_engine(config)
        from saegim.services.engines.commercial_api_engine import CommercialApiEngine

        assert isinstance(engine, CommercialApiEngine)

    @patch(f'{_MODULE}._build_vllm')
    def test_vllm_engine(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'engine_type': 'vllm',
            'vllm': {'host': 'localhost', 'port': 8000, 'model': 'datalab-to/chandra'},
        }
        result = build_engine(config)
        assert result == 'mock_engine'
        mock_build.assert_called_once_with(
            {'host': 'localhost', 'port': 8000, 'model': 'datalab-to/chandra'}
        )

    @patch(f'{_MODULE}._build_split_pipeline')
    def test_split_pipeline(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'docling_model_name': 'ibm-granite/granite-docling-258M',
                'ocr_provider': 'gemini',
                'ocr_api_key': 'test-key',
            },
        }
        result = build_engine(config)
        assert result == 'mock_engine'

    def test_unknown_engine_type_raises(self):
        with pytest.raises(ValueError, match='Unknown engine_type'):
            build_engine({'engine_type': 'unknown'})

    def test_empty_config_raises(self):
        with pytest.raises(ValueError, match='Unknown engine_type'):
            build_engine({})

    def test_missing_engine_type_raises(self):
        with pytest.raises(ValueError, match='Unknown engine_type'):
            build_engine({'some_key': 'value'})


class TestSplitPipelineOcrConfigExtraction:
    @patch(f'{_MODULE}._build_split_pipeline')
    def test_ocr_prefix_stripped(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'docling_model_name': 'ibm-granite/granite-docling-258M',
                'ocr_provider': 'gemini',
                'ocr_api_key': 'the-key',
                'ocr_model': 'gemini-3-flash-preview',
            },
        }
        build_engine(config)
        call_args = mock_build.call_args[0][0]
        assert call_args == {
            'docling_model_name': 'ibm-granite/granite-docling-258M',
            'ocr_provider': 'gemini',
            'ocr_api_key': 'the-key',
            'ocr_model': 'gemini-3-flash-preview',
        }
