"""Tests for IntegratedServerEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.integrated_server_engine import (
    IntegratedServerEngine,
    _parse_url,
)


class TestParseUrl:
    def test_basic_url(self):
        host, port = _parse_url('http://localhost:18811')
        assert host == 'localhost'
        assert port == 18811

    def test_url_with_ip(self):
        host, port = _parse_url('http://192.168.1.100:8080')
        assert host == '192.168.1.100'
        assert port == 8080

    def test_url_without_port(self):
        host, port = _parse_url('http://my-server')
        assert host == 'my-server'
        assert port == 18811  # default

    def test_url_with_path(self):
        host, port = _parse_url('http://localhost:18811/api/v1')
        assert host == 'localhost'
        assert port == 18811


class TestIntegratedServerEngine:
    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_is_base_ocr_engine_subclass(self, _mock_client, _mock_pipeline):
        engine = IntegratedServerEngine(url='http://localhost:18811')
        assert isinstance(engine, BaseOCREngine)

    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_creates_pipeline_with_builtin_ocr(self, mock_client_cls, mock_pipeline_cls):
        IntegratedServerEngine(url='http://localhost:18811')
        mock_client_cls.assert_called_once_with(host='localhost', port=18811)
        mock_pipeline_cls.assert_called_once_with(
            mock_client_cls.return_value, use_builtin_ocr=True
        )

    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_extract_page_delegates_to_pipeline(self, _mock_client, mock_pipeline_cls):
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        expected = {'layout_dets': [], 'page_attribute': {}, 'extra': {'relation': []}}
        mock_pipeline.extract_page.return_value = expected

        engine = IntegratedServerEngine(url='http://localhost:18811')
        result = engine.extract_page(Path('/fake/image.png'), 1200, 1600)

        assert result == expected
        mock_pipeline.extract_page.assert_called_once_with(
            Path('/fake/image.png'), 1200, 1600
        )

    @patch(
        'saegim.services.engines.integrated_server_engine.check_ppstructure_connection'
    )
    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_test_connection_delegates(self, _mock_client, _mock_pipeline, mock_check):
        mock_check.return_value = (True, 'Connected to PP-StructureV3')
        engine = IntegratedServerEngine(url='http://myhost:9999')

        success, message = engine.test_connection()
        assert success is True
        assert 'PP-StructureV3' in message
        mock_check.assert_called_once_with({'host': 'myhost', 'port': 9999})

    @patch(
        'saegim.services.engines.integrated_server_engine.check_ppstructure_connection'
    )
    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_test_connection_failure(self, _mock_client, _mock_pipeline, mock_check):
        mock_check.return_value = (False, 'Cannot connect')
        engine = IntegratedServerEngine(url='http://badhost:1234')

        success, message = engine.test_connection()
        assert success is False
        assert 'Cannot connect' in message
