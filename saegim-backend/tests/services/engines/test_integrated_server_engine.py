"""Tests for IntegratedServerEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.integrated_server_engine import (
    IntegratedServerEngine,
    _is_ppstructure_model,
)


class TestIsPpstructureModel:
    def test_pp_prefix_returns_true(self):
        assert _is_ppstructure_model('PP-StructureV3') is True

    def test_pp_ocr_returns_true(self):
        assert _is_ppstructure_model('PP-OCRv4') is True

    def test_chandra_returns_false(self):
        assert _is_ppstructure_model('datalab-to/chandra') is False

    def test_chandra_fp8_returns_false(self):
        assert _is_ppstructure_model('richarddavison/chandra-fp8') is False

    def test_empty_returns_false(self):
        assert _is_ppstructure_model('') is False


class TestIntegratedServerEnginePpstructure:
    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_is_base_ocr_engine_subclass(self, _mock_client, _mock_pipeline):
        engine = IntegratedServerEngine(host='localhost', port=18811, model='PP-StructureV3')
        assert isinstance(engine, BaseOCREngine)

    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_creates_pipeline_with_builtin_ocr(self, mock_client_cls, mock_pipeline_cls):
        IntegratedServerEngine(host='localhost', port=18811, model='PP-StructureV3')
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

        engine = IntegratedServerEngine(host='localhost', port=18811, model='PP-StructureV3')
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
    def test_test_connection_delegates_ppstructure(
        self, _mock_client, _mock_pipeline, mock_check
    ):
        mock_check.return_value = (True, 'Connected to PP-StructureV3')
        engine = IntegratedServerEngine(host='myhost', port=18811, model='PP-StructureV3')

        success, message = engine.test_connection()
        assert success is True
        assert 'PP-StructureV3' in message
        mock_check.assert_called_once_with({'host': 'myhost', 'port': 18811})

    @patch(
        'saegim.services.engines.integrated_server_engine.check_ppstructure_connection'
    )
    @patch('saegim.services.engines.integrated_server_engine.OcrPipeline')
    @patch('saegim.services.engines.integrated_server_engine.PpstructureClient')
    def test_test_connection_failure(self, _mock_client, _mock_pipeline, mock_check):
        mock_check.return_value = (False, 'Cannot connect')
        engine = IntegratedServerEngine(host='badhost', port=18811, model='PP-StructureV3')

        success, message = engine.test_connection()
        assert success is False
        assert 'Cannot connect' in message


class TestIntegratedServerEngineVllm:
    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_is_base_ocr_engine_subclass(self, _mock_vllm):
        engine = IntegratedServerEngine(
            host='localhost', port=8000, model='datalab-to/chandra'
        )
        assert isinstance(engine, BaseOCREngine)

    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_creates_vllm_provider(self, mock_vllm_cls):
        IntegratedServerEngine(host='vllm-host', port=8000, model='richarddavison/chandra-fp8')
        mock_vllm_cls.assert_called_once_with(
            host='vllm-host', port=8000, model='richarddavison/chandra-fp8'
        )

    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_extract_page_delegates_to_vllm_provider(self, mock_vllm_cls):
        mock_provider = MagicMock()
        mock_vllm_cls.return_value = mock_provider
        expected = {'layout_dets': [{'category_type': 'title'}], 'page_attribute': {}, 'extra': {}}
        mock_provider.extract_page.return_value = expected

        engine = IntegratedServerEngine(
            host='localhost', port=8000, model='datalab-to/chandra'
        )
        result = engine.extract_page(Path('/fake/image.png'), 1200, 1600)

        assert result == expected
        mock_provider.extract_page.assert_called_once_with(
            Path('/fake/image.png'), 1200, 1600
        )

    @patch(
        'saegim.services.engines.integrated_server_engine.check_vllm_connection'
    )
    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_test_connection_delegates_vllm(self, _mock_vllm, mock_check):
        mock_check.return_value = (True, 'Connected to vLLM (richarddavison/chandra-fp8)')
        engine = IntegratedServerEngine(
            host='vllm-host', port=8000, model='richarddavison/chandra-fp8'
        )

        success, message = engine.test_connection()
        assert success is True
        assert 'vLLM' in message
        mock_check.assert_called_once_with({'host': 'vllm-host', 'port': 8000})

    @patch(
        'saegim.services.engines.integrated_server_engine.check_vllm_connection'
    )
    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_test_connection_failure(self, _mock_vllm, mock_check):
        mock_check.return_value = (False, 'Cannot connect to vLLM')
        engine = IntegratedServerEngine(
            host='badhost', port=8000, model='datalab-to/chandra'
        )

        success, message = engine.test_connection()
        assert success is False
        assert 'Cannot connect' in message

    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_stores_model(self, _mock_vllm):
        engine = IntegratedServerEngine(
            host='localhost', port=8000, model='datalab-to/chandra'
        )
        assert engine._model == 'datalab-to/chandra'

    @patch('saegim.services.engines.integrated_server_engine.VllmOcrProvider')
    def test_default_model_uses_vllm(self, mock_vllm_cls):
        engine = IntegratedServerEngine(host='localhost', port=8000)
        assert engine._use_ppstructure is False
        mock_vllm_cls.assert_called_once()
