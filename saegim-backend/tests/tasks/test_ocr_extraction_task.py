"""Tests for OCR extraction Celery task."""

from unittest.mock import MagicMock, patch

import pytest

from saegim.tasks.ocr_extraction_task import run_ocr_extraction


class TestRunOcrExtraction:
    """Test run_ocr_extraction Celery task."""

    @patch('saegim.tasks.ocr_extraction_task._update_document_status')
    @patch('saegim.tasks.ocr_extraction_task._update_page_extraction')
    @patch('saegim.tasks.ocr_extraction_task.build_engine')
    @patch(
        'saegim.tasks.ocr_extraction_task._get_dsn',
        return_value='postgresql://test',
    )
    def test_successful_extraction(
        self,
        mock_dsn,
        mock_build_engine,
        mock_update_page,
        mock_update_doc,
    ):
        mock_engine = MagicMock()
        mock_engine.extract_page.return_value = {
            'layout_dets': [
                {
                    'category_type': 'title',
                    'poly': [10, 20, 400, 20, 400, 60, 10, 60],
                    'text': 'Title',
                    'anno_id': 0,
                    'order': 0,
                    'ignore': False,
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        mock_build_engine.return_value = mock_engine

        page_info = [
            {
                'page_id': 'page-1',
                'page_idx': 0,
                'width': 800,
                'height': 1200,
                'image_path': '/storage/images/test_p1.png',
            },
        ]
        ocr_config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test',
                'model': 'gemini-3-flash-preview',
            },
        }

        result = run_ocr_extraction.apply(args=['doc-123', page_info, ocr_config]).get()

        assert result['document_id'] == 'doc-123'
        assert result['pages_processed'] == 1
        assert result['status'] == 'ready'
        mock_update_page.assert_called_once()
        mock_update_doc.assert_called_once_with('postgresql://test', 'doc-123', 'ready')

    @patch('saegim.tasks.ocr_extraction_task._update_document_status')
    @patch('saegim.tasks.ocr_extraction_task.build_engine')
    @patch(
        'saegim.tasks.ocr_extraction_task._get_dsn',
        return_value='postgresql://test',
    )
    def test_marks_extraction_failed_after_max_retries(
        self,
        mock_dsn,
        mock_build_engine,
        mock_update_doc,
    ):
        mock_engine = MagicMock()
        mock_engine.extract_page.side_effect = RuntimeError('API failed')
        mock_build_engine.return_value = mock_engine

        page_info = [
            {
                'page_id': 'page-1',
                'page_idx': 0,
                'width': 800,
                'height': 1200,
                'image_path': '/storage/images/test_p1.png',
            },
        ]
        ocr_config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'layout_server_url': 'http://localhost:18811',
                'ocr_provider': 'vllm',
                'ocr_host': 'localhost',
                'ocr_port': 8000,
                'ocr_model': 'test',
            },
        }

        with pytest.raises(RuntimeError, match='API failed'):
            run_ocr_extraction.apply(args=['doc-fail', page_info, ocr_config]).get()

        mock_update_doc.assert_called_with('postgresql://test', 'doc-fail', 'extraction_failed')

    @patch('saegim.tasks.ocr_extraction_task._update_document_status')
    @patch('saegim.tasks.ocr_extraction_task._update_page_extraction')
    @patch('saegim.tasks.ocr_extraction_task.build_engine')
    @patch(
        'saegim.tasks.ocr_extraction_task._get_dsn',
        return_value='postgresql://test',
    )
    def test_multiple_pages_extraction(
        self,
        mock_dsn,
        mock_build_engine,
        mock_update_page,
        mock_update_doc,
    ):
        mock_engine = MagicMock()
        mock_engine.extract_page.return_value = {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        mock_build_engine.return_value = mock_engine

        page_info = [
            {
                'page_id': f'page-{i}',
                'page_idx': i,
                'width': 800,
                'height': 1200,
                'image_path': f'/storage/images/test_p{i + 1}.png',
            }
            for i in range(3)
        ]
        ocr_config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'key',
                'model': 'gemini-3-flash-preview',
            },
        }

        result = run_ocr_extraction.apply(args=['doc-multi', page_info, ocr_config]).get()

        assert result['pages_processed'] == 3
        assert mock_update_page.call_count == 3
        assert mock_engine.extract_page.call_count == 3

    @patch('saegim.tasks.ocr_extraction_task._update_document_status')
    @patch('saegim.tasks.ocr_extraction_task.build_engine')
    @patch(
        'saegim.tasks.ocr_extraction_task._get_dsn',
        return_value='postgresql://test',
    )
    def test_build_engine_raises_propagates(
        self,
        mock_dsn,
        mock_build_engine,
        mock_update_doc,
    ):
        mock_build_engine.side_effect = ValueError('Unknown engine_type')

        page_info = [
            {
                'page_id': 'page-1',
                'page_idx': 0,
                'width': 800,
                'height': 1200,
                'image_path': '/storage/images/test_p1.png',
            },
        ]
        ocr_config = {'engine_type': 'bad_type'}

        with pytest.raises(ValueError, match='Unknown engine_type'):
            run_ocr_extraction.apply(args=['doc-bad', page_info, ocr_config]).get()
