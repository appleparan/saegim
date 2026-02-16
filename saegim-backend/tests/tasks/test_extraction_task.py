"""Tests for MinerU extraction Celery task."""

from unittest.mock import MagicMock, call, patch

import pytest

from saegim.tasks.extraction_task import (
    _update_document_status,
    _update_page_extraction,
    run_mineru_extraction,
)


class TestUpdatePageExtraction:
    """Tests for _update_page_extraction helper."""

    @patch('saegim.tasks.extraction_task.psycopg')
    def test_updates_page_with_extracted_data(self, mock_psycopg):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_psycopg.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        data = {'layout_dets': [], 'page_attribute': {}, 'extra': {'relation': []}}
        _update_page_extraction('postgresql://test', 'page-uuid', data)

        mock_cur.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestUpdateDocumentStatus:
    """Tests for _update_document_status helper."""

    @patch('saegim.tasks.extraction_task.psycopg')
    def test_updates_document_status(self, mock_psycopg):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_psycopg.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_psycopg.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        _update_document_status('postgresql://test', 'doc-uuid', 'ready')

        mock_cur.execute.assert_called_once()
        args = mock_cur.execute.call_args[0]
        assert args[1] == ('ready', 'doc-uuid')
        mock_conn.commit.assert_called_once()


class TestRunMineruExtraction:
    """Tests for the run_mineru_extraction Celery task."""

    @patch('saegim.tasks.extraction_task._update_document_status')
    @patch('saegim.tasks.extraction_task._update_page_extraction')
    @patch('saegim.tasks.extraction_task.mineru_extraction_service')
    @patch('saegim.tasks.extraction_task._get_dsn', return_value='postgresql://test')
    def test_successful_extraction(
        self, mock_dsn, mock_service, mock_update_page, mock_update_doc
    ):
        mock_service.extract_document.return_value = {
            0: {
                'layout_dets': [{'category_type': 'text_block', 'anno_id': 0}],
                'page_attribute': {},
                'extra': {'relation': []},
            },
        }

        page_info = [
            {'page_id': 'page-1', 'page_idx': 0, 'width': 2000, 'height': 3000},
        ]

        result = run_mineru_extraction.apply(
            args=['doc-1', '/tmp/test.pdf', page_info, 'korean', 'pipeline']
        ).get()

        assert result['document_id'] == 'doc-1'
        assert result['pages_processed'] == 1
        assert result['status'] == 'ready'

        mock_update_page.assert_called_once()
        mock_update_doc.assert_called_once_with('postgresql://test', 'doc-1', 'ready')

    @patch('saegim.tasks.extraction_task._update_document_status')
    @patch('saegim.tasks.extraction_task._update_page_extraction')
    @patch('saegim.tasks.extraction_task.mineru_extraction_service')
    @patch('saegim.tasks.extraction_task._get_dsn', return_value='postgresql://test')
    def test_multi_page_extraction(
        self, mock_dsn, mock_service, mock_update_page, mock_update_doc
    ):
        mock_service.extract_document.return_value = {
            0: {'layout_dets': [{'anno_id': 0}], 'page_attribute': {}, 'extra': {'relation': []}},
            1: {'layout_dets': [{'anno_id': 0}], 'page_attribute': {}, 'extra': {'relation': []}},
        }

        page_info = [
            {'page_id': 'page-1', 'page_idx': 0, 'width': 2000, 'height': 3000},
            {'page_id': 'page-2', 'page_idx': 1, 'width': 2000, 'height': 3000},
        ]

        result = run_mineru_extraction.apply(
            args=['doc-1', '/tmp/test.pdf', page_info, 'korean', 'pipeline']
        ).get()

        assert result['pages_processed'] == 2
        assert mock_update_page.call_count == 2

    @patch('saegim.tasks.extraction_task._update_document_status')
    @patch('saegim.tasks.extraction_task.mineru_extraction_service')
    @patch('saegim.tasks.extraction_task._get_dsn', return_value='postgresql://test')
    def test_marks_extraction_failed_after_max_retries(
        self, mock_dsn, mock_service, mock_update_doc
    ):
        mock_service.extract_document.side_effect = RuntimeError('MinerU crashed')

        page_info = [
            {'page_id': 'page-1', 'page_idx': 0, 'width': 2000, 'height': 3000},
        ]

        with pytest.raises(RuntimeError, match='MinerU crashed'):
            run_mineru_extraction.apply(
                args=['doc-1', '/tmp/test.pdf', page_info, 'korean', 'pipeline']
            ).get()

        mock_update_doc.assert_called_with('postgresql://test', 'doc-1', 'extraction_failed')

    @patch('saegim.tasks.extraction_task._update_document_status')
    @patch('saegim.tasks.extraction_task._update_page_extraction')
    @patch('saegim.tasks.extraction_task.mineru_extraction_service')
    @patch('saegim.tasks.extraction_task._get_dsn', return_value='postgresql://test')
    def test_missing_page_gets_empty_result(
        self, mock_dsn, mock_service, mock_update_page, mock_update_doc
    ):
        # MinerU returns no results for page 1
        mock_service.extract_document.return_value = {
            0: {'layout_dets': [{'anno_id': 0}], 'page_attribute': {}, 'extra': {'relation': []}},
        }

        page_info = [
            {'page_id': 'page-1', 'page_idx': 0, 'width': 2000, 'height': 3000},
            {'page_id': 'page-2', 'page_idx': 1, 'width': 2000, 'height': 3000},
        ]

        result = run_mineru_extraction.apply(
            args=['doc-1', '/tmp/test.pdf', page_info, 'korean', 'pipeline']
        ).get()

        assert result['pages_processed'] == 2
        # Page 2 should get empty layout_dets
        page2_call = mock_update_page.call_args_list[1]
        extracted_data = page2_call[0][2]
        assert extracted_data['layout_dets'] == []
