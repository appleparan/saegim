"""Tests for engine factory."""

from unittest.mock import patch

import pytest

from saegim.services.engines.factory import build_engine_by_id

_MODULE = 'saegim.services.engines.factory'


class TestBuildEngineById:
    def test_pdfminer_when_no_default(self):
        config = {'default_engine_id': None, 'engines': {}}
        engine = build_engine_by_id(config)
        from saegim.services.engines.pdfminer_engine import PdfminerEngine

        assert isinstance(engine, PdfminerEngine)

    def test_pdfminer_when_default_is_pdfminer(self):
        config = {'default_engine_id': 'pdfminer', 'engines': {}}
        engine = build_engine_by_id(config)
        from saegim.services.engines.pdfminer_engine import PdfminerEngine

        assert isinstance(engine, PdfminerEngine)

    def test_commercial_api_by_id(self):
        config = {
            'default_engine_id': 'gemini-flash',
            'engines': {
                'gemini-flash': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Flash',
                    'config': {
                        'provider': 'gemini',
                        'api_key': 'test-key',
                        'model': 'gemini-3-flash-preview',
                    },
                },
            },
        }
        engine = build_engine_by_id(config)
        from saegim.services.engines.commercial_api_engine import CommercialApiEngine

        assert isinstance(engine, CommercialApiEngine)

    @patch(f'{_MODULE}._build_vllm')
    def test_vllm_by_id(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'default_engine_id': 'my-vllm',
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'gpu-server', 'port': 8000, 'model': 'test-model'},
                },
            },
        }
        result = build_engine_by_id(config)
        assert result == 'mock_engine'
        mock_build.assert_called_once_with(
            {'host': 'gpu-server', 'port': 8000, 'model': 'test-model'}
        )

    def test_explicit_engine_id_overrides_default(self):
        config = {
            'default_engine_id': 'gemini-flash',
            'engines': {
                'gemini-flash': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Flash',
                    'config': {'provider': 'gemini', 'api_key': 'k', 'model': 'm'},
                },
                'my-pdfminer': {
                    'engine_type': 'pdfminer',
                    'name': 'Pdfminer',
                    'config': {},
                },
            },
        }
        from saegim.services.engines.pdfminer_engine import PdfminerEngine

        engine = build_engine_by_id(config, engine_id='pdfminer')
        assert isinstance(engine, PdfminerEngine)

    def test_engine_id_not_found_raises(self):
        config = {
            'default_engine_id': 'gemini-flash',
            'engines': {
                'gemini-flash': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Flash',
                    'config': {'provider': 'gemini', 'api_key': 'k', 'model': 'm'},
                },
            },
        }
        with pytest.raises(ValueError, match='not found in config'):
            build_engine_by_id(config, engine_id='nonexistent')

    def test_unknown_engine_type_in_entry_raises(self):
        config = {
            'default_engine_id': 'bad-engine',
            'engines': {
                'bad-engine': {
                    'engine_type': 'unknown_type',
                    'name': 'Bad',
                    'config': {},
                },
            },
        }
        with pytest.raises(ValueError, match='Unknown engine_type'):
            build_engine_by_id(config)


class TestBuildEngineFromType:
    @patch(f'{_MODULE}._build_split_pipeline')
    def test_ocr_prefix_stripped(self, mock_build):
        mock_build.return_value = 'mock_engine'
        config = {
            'default_engine_id': 'split-1',
            'engines': {
                'split-1': {
                    'engine_type': 'split_pipeline',
                    'name': 'Split Pipeline',
                    'config': {
                        'docling_model_name': 'ibm-granite/granite-docling-258M',
                        'ocr_provider': 'gemini',
                        'ocr_api_key': 'the-key',
                        'ocr_model': 'gemini-3-flash-preview',
                    },
                },
            },
        }
        build_engine_by_id(config)
        call_args = mock_build.call_args[0][0]
        assert call_args == {
            'docling_model_name': 'ibm-granite/granite-docling-258M',
            'ocr_provider': 'gemini',
            'ocr_api_key': 'the-key',
            'ocr_model': 'gemini-3-flash-preview',
        }


_SPLIT_ENGINE = 'saegim.services.engines.split_pipeline_engine.SplitPipelineEngine'


class TestSplitPipelineLayoutProvider:
    @patch(_SPLIT_ENGINE, autospec=True)
    def test_layout_provider_passed_to_engine(self, mock_cls):
        mock_cls.return_value = mock_cls
        config = {
            'docling_model_name': 'ibm-granite/granite-docling-258M',
            'ocr_provider': 'gemini',
            'ocr_api_key': 'key',
            'layout_provider': 'pp_doclayout',
        }
        from saegim.services.engines.factory import _build_split_pipeline

        _build_split_pipeline(config)
        mock_cls.assert_called_once()
        assert mock_cls.call_args.kwargs['layout_provider'] == 'pp_doclayout'

    @patch(_SPLIT_ENGINE, autospec=True)
    def test_layout_provider_defaults_to_docling(self, mock_cls):
        mock_cls.return_value = mock_cls
        config = {
            'docling_model_name': 'ibm-granite/granite-docling-258M',
            'ocr_provider': 'gemini',
            'ocr_api_key': 'key',
        }
        from saegim.services.engines.factory import _build_split_pipeline

        _build_split_pipeline(config)
        assert mock_cls.call_args.kwargs['layout_provider'] == 'docling'
