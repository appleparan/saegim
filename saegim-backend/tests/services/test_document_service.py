"""Tests for document upload and PDF conversion service."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from saegim.services import document_service


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.fixture
def document_id():
    return uuid.uuid4()


class TestUploadAndConvert:
    @pytest.mark.asyncio
    async def test_creates_storage_directories(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_page = MagicMock()
            mock_pix = MagicMock()
            mock_pix.width = 800
            mock_pix.height = 1000
            mock_page.get_pixmap.return_value = mock_pix

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, i: mock_page
            mock_fitz.open.return_value = mock_pdf
            mock_fitz.Matrix.return_value = MagicMock()

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF-fake', str(tmp_path),
            )

        assert (tmp_path / 'pdfs').is_dir()
        assert (tmp_path / 'images').is_dir()

    @pytest.mark.asyncio
    async def test_saves_pdf_to_disk(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}
        pdf_bytes = b'%PDF-1.4 fake content'

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_fitz.open.return_value = mock_pdf

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', pdf_bytes, str(tmp_path),
            )

        pdf_file = tmp_path / 'pdfs' / f'{doc_id}_test.pdf'
        assert pdf_file.exists()
        assert pdf_file.read_bytes() == pdf_bytes

    @pytest.mark.asyncio
    async def test_creates_document_record_with_processing_status(
        self, mock_pool, project_id, tmp_path,
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo'),
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_fitz.open.return_value = mock_pdf

            await document_service.upload_and_convert(
                mock_pool, project_id, 'report.pdf', b'%PDF', str(tmp_path),
            )

        mock_doc_repo.create.assert_called_once_with(
            mock_pool,
            project_id=project_id,
            filename='report.pdf',
            pdf_path=str(tmp_path / 'pdfs' / f'{doc_id}_report.pdf'),
            status='processing',
        )

    @pytest.mark.asyncio
    async def test_converts_pages_to_images(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pix = MagicMock()
            mock_pix.width = 1200
            mock_pix.height = 1600

            mock_page1 = MagicMock()
            mock_page1.get_pixmap.return_value = mock_pix
            mock_page2 = MagicMock()
            mock_page2.get_pixmap.return_value = mock_pix

            pages = [mock_page1, mock_page2]
            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 2
            mock_pdf.__getitem__ = lambda _, i: pages[i]
            mock_fitz.open.return_value = mock_pdf
            mock_fitz.Matrix.return_value = MagicMock()

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path),
            )

        assert mock_page_repo.create.call_count == 2

        call1 = mock_page_repo.create.call_args_list[0]
        assert call1.kwargs['page_no'] == 1
        assert call1.kwargs['width'] == 1200
        assert call1.kwargs['height'] == 1600

        call2 = mock_page_repo.create.call_args_list[1]
        assert call2.kwargs['page_no'] == 2

    @pytest.mark.asyncio
    async def test_uses_2x_matrix_for_rendering(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pix = MagicMock()
            mock_pix.width = 800
            mock_pix.height = 1000

            mock_page = MagicMock()
            mock_page.get_pixmap.return_value = mock_pix

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, i: mock_page
            mock_fitz.open.return_value = mock_pdf

            matrix_instance = MagicMock()
            mock_fitz.Matrix.return_value = matrix_instance

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path),
            )

        mock_fitz.Matrix.assert_called_once_with(2.0, 2.0)
        mock_page.get_pixmap.assert_called_once_with(matrix=matrix_instance)

    @pytest.mark.asyncio
    async def test_updates_status_to_ready_on_success(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pix = MagicMock()
            mock_pix.width = 800
            mock_pix.height = 1000
            mock_page = MagicMock()
            mock_page.get_pixmap.return_value = mock_pix

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 3
            mock_pdf.__getitem__ = lambda _, i: mock_page
            mock_fitz.open.return_value = mock_pdf
            mock_fitz.Matrix.return_value = MagicMock()

            mock_page_repo.create = AsyncMock()

            result = await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path),
            )

        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=doc_id, status='ready', total_pages=3,
        )
        assert result == {
            'id': doc_id,
            'filename': 'test.pdf',
            'total_pages': 3,
            'status': 'ready',
        }

    @pytest.mark.asyncio
    async def test_updates_status_to_error_on_failure(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo'),
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()
            mock_fitz.open.side_effect = RuntimeError('Corrupt PDF')

            with pytest.raises(RuntimeError, match='Corrupt PDF'):
                await document_service.upload_and_convert(
                    mock_pool, project_id, 'bad.pdf', b'bad', str(tmp_path),
                )

        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=doc_id, status='error',
        )

    @pytest.mark.asyncio
    async def test_returns_correct_result_dict(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'fitz') as mock_fitz,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_fitz.open.return_value = mock_pdf
            mock_page_repo.create = AsyncMock()

            result = await document_service.upload_and_convert(
                mock_pool, project_id, 'empty.pdf', b'%PDF', str(tmp_path),
            )

        assert result['id'] == doc_id
        assert result['filename'] == 'empty.pdf'
        assert result['total_pages'] == 0
        assert result['status'] == 'ready'
