"""Tests for VllmEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.vllm_engine import VllmEngine

_MODULE = 'saegim.services.engines.vllm_engine'


class TestVllmEngineInit:
    @patch(f'{_MODULE}.VllmOcrProvider')
    def test_default_params(self, mock_provider_cls):
        engine = VllmEngine()
        assert isinstance(engine, BaseOCREngine)
        mock_provider_cls.assert_called_once_with(
            host='localhost', port=8000, model='datalab-to/chandra'
        )

    @patch(f'{_MODULE}.VllmOcrProvider')
    def test_custom_params(self, mock_provider_cls):
        engine = VllmEngine(host='gpu-server', port=9000, model='custom/model')
        assert isinstance(engine, BaseOCREngine)
        mock_provider_cls.assert_called_once_with(
            host='gpu-server', port=9000, model='custom/model'
        )


class TestVllmEngineExtractPage:
    @patch(f'{_MODULE}.VllmOcrProvider')
    def test_delegates_to_provider(self, mock_provider_cls):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider
        expected = {'layout_dets': [{'text': 'test'}], 'page_attribute': {}, 'extra': {}}
        mock_provider.extract_page.return_value = expected

        engine = VllmEngine()
        result = engine.extract_page(Path('/fake/image.png'), 1200, 1600)

        assert result == expected
        mock_provider.extract_page.assert_called_once_with(Path('/fake/image.png'), 1200, 1600)


class TestVllmEngineTestConnection:
    @patch(f'{_MODULE}.check_vllm_connection')
    @patch(f'{_MODULE}.VllmOcrProvider')
    def test_successful_connection(self, mock_provider_cls, mock_check):
        mock_check.return_value = (True, 'Connected to localhost:8000')
        engine = VllmEngine()
        success, message = engine.test_connection()

        assert success is True
        assert 'localhost:8000' in message
        mock_check.assert_called_once_with({'host': 'localhost', 'port': 8000})

    @patch(f'{_MODULE}.check_vllm_connection')
    @patch(f'{_MODULE}.VllmOcrProvider')
    def test_failed_connection(self, mock_provider_cls, mock_check):
        mock_check.return_value = (False, 'Cannot connect')
        engine = VllmEngine(host='bad-host', port=9999)
        success, message = engine.test_connection()

        assert success is False
        assert 'Cannot connect' in message
