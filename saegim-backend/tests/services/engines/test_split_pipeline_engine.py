"""Tests for SplitPipelineEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.split_pipeline_engine import SplitPipelineEngine


_MODULE = 'saegim.services.engines.split_pipeline_engine'


class TestSplitPipelineEngineInit:
    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_gemini_creates_engine(self, mock_text, _mock_client, _mock_pipeline):
        mock_text.return_value = MagicMock()
        config = {'api_key': 'test-key', 'model': 'gemini-2.0-flash'}
        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='gemini',
            ocr_config=config,
        )
        assert isinstance(engine, BaseOCREngine)

    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_vllm_creates_engine(self, mock_text, _mock_client, _mock_pipeline):
        mock_text.return_value = MagicMock()
        config = {'host': 'localhost', 'port': 8000}
        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='vllm',
            ocr_config=config,
        )
        assert isinstance(engine, BaseOCREngine)

    def test_unknown_ocr_provider_raises(self):
        with pytest.raises(ValueError, match='Unknown split pipeline OCR provider'):
            SplitPipelineEngine(
                layout_server_url='http://localhost:18811',
                ocr_provider='unknown',
                ocr_config={},
            )

    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_creates_pipeline_with_text_provider(
        self, mock_text, mock_client_cls, mock_pipeline_cls
    ):
        mock_text_provider = MagicMock()
        mock_text.return_value = mock_text_provider

        SplitPipelineEngine(
            layout_server_url='http://myhost:9999',
            ocr_provider='gemini',
            ocr_config={'api_key': 'k'},
        )
        mock_client_cls.assert_called_once_with(host='myhost', port=9999)
        mock_pipeline_cls.assert_called_once_with(
            mock_client_cls.return_value, mock_text_provider
        )


class TestSplitPipelineEngineExtractPage:
    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_delegates_to_pipeline(self, mock_text, _mock_client, mock_pipeline_cls):
        mock_text.return_value = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        expected = {'layout_dets': [{'text': 'cropped'}], 'page_attribute': {}, 'extra': {}}
        mock_pipeline.extract_page.return_value = expected

        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='gemini',
            ocr_config={'api_key': 'k'},
        )
        result = engine.extract_page(Path('/fake/image.png'), 1200, 1600)

        assert result == expected
        mock_pipeline.extract_page.assert_called_once_with(
            Path('/fake/image.png'), 1200, 1600
        )


class TestSplitPipelineEngineTestConnection:
    @patch(f'{_MODULE}._check_ocr_provider')
    @patch(f'{_MODULE}.check_ppstructure_connection')
    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_both_succeed(
        self, mock_text, _mock_client, _mock_pipeline, mock_layout_check, mock_ocr_check
    ):
        mock_text.return_value = MagicMock()
        mock_layout_check.return_value = (True, 'Layout OK')
        mock_ocr_check.return_value = (True, 'OCR OK')

        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='gemini',
            ocr_config={'api_key': 'k'},
        )
        success, message = engine.test_connection()

        assert success is True
        assert 'Layout OK' in message
        assert 'OCR OK' in message

    @patch(f'{_MODULE}.check_ppstructure_connection')
    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_layout_fails_fast(
        self, mock_text, _mock_client, _mock_pipeline, mock_layout_check
    ):
        mock_text.return_value = MagicMock()
        mock_layout_check.return_value = (False, 'Layout down')

        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='gemini',
            ocr_config={'api_key': 'k'},
        )
        success, message = engine.test_connection()

        assert success is False
        assert 'Layout down' in message

    @patch(f'{_MODULE}._check_ocr_provider')
    @patch(f'{_MODULE}.check_ppstructure_connection')
    @patch(f'{_MODULE}.OcrPipeline')
    @patch(f'{_MODULE}.PpstructureClient')
    @patch(f'{_MODULE}._create_text_provider')
    def test_ocr_fails(
        self, mock_text, _mock_client, _mock_pipeline, mock_layout_check, mock_ocr_check
    ):
        mock_text.return_value = MagicMock()
        mock_layout_check.return_value = (True, 'Layout OK')
        mock_ocr_check.return_value = (False, 'OCR down')

        engine = SplitPipelineEngine(
            layout_server_url='http://localhost:18811',
            ocr_provider='gemini',
            ocr_config={'api_key': 'k'},
        )
        success, message = engine.test_connection()

        assert success is False
        assert 'OCR down' in message
