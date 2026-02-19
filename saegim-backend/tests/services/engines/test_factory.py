"""Tests for engine factory."""

from unittest.mock import patch

import pytest

from saegim.services.engines.factory import build_engine


_MODULE = 'saegim.services.engines.factory'


class TestBuildEngine:
    def test_pymupdf_engine(self):
        engine = build_engine({'engine_type': 'pymupdf'})
        from saegim.services.engines.pymupdf_engine import PyMuPDFEngine

        assert isinstance(engine, PyMuPDFEngine)

    def test_commercial_api_gemini(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-2.0-flash',
            },
        }
        engine = build_engine(config)
        from saegim.services.engines.commercial_api_engine import CommercialApiEngine

        assert isinstance(engine, CommercialApiEngine)

    def test_commercial_api_vllm(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'vllm',
                'host': 'localhost',
                'port': 8000,
                'model': 'test-model',
            },
        }
        engine = build_engine(config)
        from saegim.services.engines.commercial_api_engine import CommercialApiEngine

        assert isinstance(engine, CommercialApiEngine)

    @patch(f'{_MODULE}._build_integrated_server')
    def test_integrated_server(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'engine_type': 'integrated_server',
            'integrated_server': {'url': 'http://localhost:18811'},
        }
        result = build_engine(config)
        assert result == 'mock_engine'
        mock_build.assert_called_once_with({'url': 'http://localhost:18811'})

    @patch(f'{_MODULE}._build_split_pipeline')
    def test_split_pipeline(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'layout_server_url': 'http://localhost:18811',
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
                'layout_server_url': 'http://localhost:18811',
                'ocr_provider': 'gemini',
                'ocr_api_key': 'the-key',
                'ocr_model': 'gemini-2.0-flash',
            },
        }
        build_engine(config)
        call_args = mock_build.call_args[0][0]
        assert call_args == {
            'layout_server_url': 'http://localhost:18811',
            'ocr_provider': 'gemini',
            'ocr_api_key': 'the-key',
            'ocr_model': 'gemini-2.0-flash',
        }
