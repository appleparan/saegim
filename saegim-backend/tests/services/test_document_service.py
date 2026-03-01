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


@pytest.fixture
def mock_pdfminer_config():
    return {'engine_type': 'pdfminer'}


@pytest.fixture
def mock_ocr_settings():
    settings = MagicMock()
    return settings


class TestUploadAndConvert:
    @pytest.mark.asyncio
    async def test_creates_storage_directories(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service, 'extraction_service') as mock_ext,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_ext.extract_page_elements.return_value = {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            }
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool,
                project_id,
                'test.pdf',
                b'%PDF-fake',
                str(tmp_path),
            )

        assert (tmp_path / 'pdfs').is_dir()
        assert (tmp_path / 'images').is_dir()

    @pytest.mark.asyncio
    async def test_saves_pdf_to_disk(self, mock_pool, project_id, tmp_path, mock_pdfminer_config):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}
        pdf_bytes = b'%PDF-1.4 fake content'

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool,
                project_id,
                'test.pdf',
                pdf_bytes,
                str(tmp_path),
            )

        pdf_file = tmp_path / 'pdfs' / f'{doc_id}_test.pdf'
        assert pdf_file.exists()
        assert pdf_file.read_bytes() == pdf_bytes

    @pytest.mark.asyncio
    async def test_creates_document_record_with_processing_status(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo'),
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_pdfium.PdfDocument.return_value = mock_pdf

            await document_service.upload_and_convert(
                mock_pool, project_id, 'report.pdf', b'%PDF', str(tmp_path)
            )

        mock_doc_repo.create.assert_called_once_with(
            mock_pool,
            project_id=project_id,
            filename='report.pdf',
            pdf_path=str(tmp_path / 'pdfs' / f'{doc_id}_report.pdf'),
            status='processing',
        )

    @pytest.mark.asyncio
    async def test_converts_pages_to_images(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service, 'extraction_service') as mock_ext,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_ext.extract_page_elements.return_value = {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            }
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (1200, 1600)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page1 = MagicMock()
            mock_page1.render.return_value = mock_bitmap
            mock_page2 = MagicMock()
            mock_page2.render.return_value = mock_bitmap

            pages = [mock_page1, mock_page2]
            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 2
            mock_pdf.__getitem__ = lambda _, i: pages[i]
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        assert mock_page_repo.create.call_count == 2
        assert mock_page_repo.create.call_args_list[0].kwargs['page_no'] == 1
        assert mock_page_repo.create.call_args_list[0].kwargs['width'] == 1200
        assert mock_page_repo.create.call_args_list[1].kwargs['page_no'] == 2

    @pytest.mark.asyncio
    async def test_uses_2x_scale_for_rendering(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service, 'extraction_service') as mock_ext,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_ext.extract_page_elements.return_value = {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            }
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock()

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        mock_page.render.assert_called_once_with(scale=2.0)

    @pytest.mark.asyncio
    async def test_updates_status_to_ready_on_success(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service, 'extraction_service') as mock_ext,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_ext.extract_page_elements.return_value = {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            }
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 3
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf
            mock_page_repo.create = AsyncMock()

            result = await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=doc_id, status='ready', total_pages=3
        )
        assert result == {
            'id': doc_id,
            'filename': 'test.pdf',
            'total_pages': 3,
            'status': 'ready',
        }

    @pytest.mark.asyncio
    async def test_updates_status_to_error_on_failure(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo'),
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()
            mock_pdfium.PdfDocument.side_effect = RuntimeError('Corrupt PDF')

            with pytest.raises(RuntimeError, match='Corrupt PDF'):
                await document_service.upload_and_convert(
                    mock_pool, project_id, 'bad.pdf', b'bad', str(tmp_path)
                )

        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=doc_id, status='error'
        )

    @pytest.mark.asyncio
    async def test_returns_correct_result_dict(
        self, mock_pool, project_id, tmp_path, mock_pdfminer_config
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value=mock_pdfminer_config,
            ),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 0
            mock_pdfium.PdfDocument.return_value = mock_pdf
            mock_page_repo.create = AsyncMock()

            result = await document_service.upload_and_convert(
                mock_pool, project_id, 'empty.pdf', b'%PDF', str(tmp_path)
            )

        assert result['id'] == doc_id
        assert result['filename'] == 'empty.pdf'
        assert result['total_pages'] == 0
        assert result['status'] == 'ready'


class TestUploadAndConvertOcr:
    @pytest.mark.asyncio
    async def test_creates_background_task_for_ocr(
        self, mock_pool, project_id, tmp_path, mock_ocr_settings
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}
        page_record = {'id': uuid.uuid4()}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={
                    'engine_type': 'commercial_api',
                    'commercial_api': {
                        'provider': 'gemini',
                        'api_key': 'k',
                        'model': 'm',
                    },
                },
            ),
            patch.object(
                document_service.asyncio,
                'create_task',
                side_effect=lambda coro: (coro.close(), MagicMock())[-1],
            ) as mock_create_task,
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock(return_value=page_record)

            result = await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        assert result['status'] == 'extracting'
        mock_create_task.assert_called_once()
        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=doc_id, status='extracting', total_pages=1
        )

    @pytest.mark.asyncio
    async def test_does_not_call_pdfminer_extraction_for_ocr_engine(
        self, mock_pool, project_id, tmp_path, mock_ocr_settings
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}
        page_record = {'id': uuid.uuid4()}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={
                    'engine_type': 'split_pipeline',
                    'split_pipeline': {
                        'layout_server_url': 'http://localhost:18811',
                        'ocr_provider': 'vllm',
                        'ocr_host': 'h',
                        'ocr_port': 8000,
                        'ocr_model': 'm',
                    },
                },
            ),
            patch.object(
                document_service.asyncio,
                'create_task',
                side_effect=lambda coro: (coro.close(), MagicMock())[-1],
            ),
            patch.object(document_service, 'extraction_service') as mock_ext,
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock(return_value=page_record)

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        mock_ext.extract_page_elements.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_pages_without_extracted_data(
        self, mock_pool, project_id, tmp_path, mock_ocr_settings
    ):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id}
        page_record = {'id': uuid.uuid4()}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'pdfium') as mock_pdfium,
            patch.object(document_service.uuid, 'uuid4', return_value=doc_id),
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={
                    'engine_type': 'commercial_api',
                    'commercial_api': {
                        'provider': 'gemini',
                        'api_key': 'k',
                        'model': 'm',
                    },
                },
            ),
            patch.object(
                document_service.asyncio,
                'create_task',
                side_effect=lambda coro: (coro.close(), MagicMock())[-1],
            ),
        ):
            mock_doc_repo.create = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()

            mock_pil = MagicMock()
            mock_pil.size = (800, 1000)

            mock_bitmap = MagicMock()
            mock_bitmap.to_pil.return_value = mock_pil

            mock_page = MagicMock()
            mock_page.render.return_value = mock_bitmap

            mock_pdf = MagicMock()
            mock_pdf.__len__ = lambda _: 1
            mock_pdf.__getitem__ = lambda _, _i: mock_page
            mock_pdfium.PdfDocument.return_value = mock_pdf

            mock_page_repo.create = AsyncMock(return_value=page_record)

            await document_service.upload_and_convert(
                mock_pool, project_id, 'test.pdf', b'%PDF', str(tmp_path)
            )

        assert mock_page_repo.create.call_args.kwargs['auto_extracted_data'] is None


class TestReExtract:
    @pytest.mark.asyncio
    async def test_raises_when_document_not_found(self, mock_pool, document_id):
        with patch.object(document_service, 'document_repo') as mock_doc_repo:
            mock_doc_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(LookupError, match='not found'):
                await document_service.re_extract(mock_pool, document_id)

    @pytest.mark.asyncio
    async def test_raises_when_already_extracting(self, mock_pool, document_id, project_id):
        doc_record = {
            'id': document_id,
            'project_id': project_id,
            'pdf_path': '/fake.pdf',
            'status': 'extracting',
        }
        with patch.object(document_service, 'document_repo') as mock_doc_repo:
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)

            with pytest.raises(ValueError, match='already extracting'):
                await document_service.re_extract(mock_pool, document_id)

    @pytest.mark.asyncio
    async def test_raises_when_no_pages(self, mock_pool, document_id, project_id):
        doc_record = {
            'id': document_id,
            'project_id': project_id,
            'pdf_path': '/fake.pdf',
            'status': 'ready',
        }
        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={'engine_type': 'pdfminer'},
            ),
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_page_repo.list_for_extraction = AsyncMock(return_value=[])

            with pytest.raises(LookupError, match='no pages'):
                await document_service.re_extract(mock_pool, document_id)

    @pytest.mark.asyncio
    async def test_pdfminer_re_extract_returns_ready(self, mock_pool, document_id, project_id):
        doc_record = {
            'id': document_id,
            'project_id': project_id,
            'pdf_path': '/fake.pdf',
            'status': 'ready',
        }
        page_records = [
            {
                'id': uuid.uuid4(),
                'page_no': 1,
                'width': 800,
                'height': 1000,
                'image_path': '/img.png',
            },
        ]
        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(document_service, 'extraction_service') as mock_ext,
            patch.object(document_service, 'attribute_classifier') as mock_cls,
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={'engine_type': 'pdfminer'},
            ),
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()
            mock_page_repo.list_for_extraction = AsyncMock(return_value=page_records)
            mock_page_repo.update_auto_extracted_data = AsyncMock()
            mock_ext.extract_page_elements.return_value = {'layout_dets': []}
            mock_cls.classify_attributes.return_value = {'layout_dets': []}

            result = await document_service.re_extract(mock_pool, document_id)

        assert result['status'] == 'ready'
        mock_ext.extract_page_elements.assert_called_once()
        mock_page_repo.update_auto_extracted_data.assert_called_once()
        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=document_id, status='ready'
        )

    @pytest.mark.asyncio
    async def test_ocr_re_extract_creates_background_task(self, mock_pool, document_id, project_id):
        doc_record = {
            'id': document_id,
            'project_id': project_id,
            'pdf_path': '/fake.pdf',
            'status': 'ready',
        }
        page_records = [
            {
                'id': uuid.uuid4(),
                'page_no': 1,
                'width': 800,
                'height': 1000,
                'image_path': '/img.png',
            },
        ]
        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
            patch.object(
                document_service,
                '_resolve_ocr_config',
                new_callable=AsyncMock,
                return_value={
                    'engine_type': 'commercial_api',
                    'commercial_api': {'provider': 'gemini', 'api_key': 'k', 'model': 'm'},
                },
            ),
            patch.object(
                document_service.asyncio,
                'create_task',
                side_effect=lambda coro: (coro.close(), MagicMock())[-1],
            ) as mock_create_task,
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_doc_repo.update_status = AsyncMock()
            mock_page_repo.list_for_extraction = AsyncMock(return_value=page_records)

            result = await document_service.re_extract(mock_pool, document_id)

        assert result['status'] == 'extracting'
        mock_create_task.assert_called_once()
        mock_doc_repo.update_status.assert_called_once_with(
            mock_pool, document_id=document_id, status='extracting'
        )


class TestDeleteWithFiles:
    @pytest.mark.asyncio
    async def test_returns_false_when_document_not_found(self, mock_pool):
        doc_id = uuid.uuid4()

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=None)

            result = await document_service.delete_with_files(mock_pool, doc_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_deletes_document_and_files(self, mock_pool, tmp_path):
        doc_id = uuid.uuid4()

        # Create actual files to verify deletion
        pdf_file = tmp_path / 'test.pdf'
        pdf_file.write_bytes(b'%PDF')
        img_file = tmp_path / 'page1.png'
        img_file.write_bytes(b'PNG')

        doc_record = {'id': doc_id, 'pdf_path': str(pdf_file)}
        page_records = [{'image_path': str(img_file)}]

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_doc_repo.delete = AsyncMock(return_value=True)
            mock_page_repo.list_by_document = AsyncMock(return_value=page_records)

            result = await document_service.delete_with_files(mock_pool, doc_id)

        assert result is True
        assert not pdf_file.exists()
        assert not img_file.exists()

    @pytest.mark.asyncio
    async def test_does_not_delete_files_when_db_delete_fails(self, mock_pool, tmp_path):
        doc_id = uuid.uuid4()

        pdf_file = tmp_path / 'test.pdf'
        pdf_file.write_bytes(b'%PDF')

        doc_record = {'id': doc_id, 'pdf_path': str(pdf_file)}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_doc_repo.delete = AsyncMock(return_value=False)
            mock_page_repo.list_by_document = AsyncMock(return_value=[])

            result = await document_service.delete_with_files(mock_pool, doc_id)

        assert result is False
        assert pdf_file.exists()

    @pytest.mark.asyncio
    async def test_handles_no_pdf_path(self, mock_pool):
        doc_id = uuid.uuid4()
        doc_record = {'id': doc_id, 'pdf_path': None}

        with (
            patch.object(document_service, 'document_repo') as mock_doc_repo,
            patch.object(document_service, 'page_repo') as mock_page_repo,
        ):
            mock_doc_repo.get_by_id = AsyncMock(return_value=doc_record)
            mock_doc_repo.delete = AsyncMock(return_value=True)
            mock_page_repo.list_by_document = AsyncMock(return_value=[])

            result = await document_service.delete_with_files(mock_pool, doc_id)

        assert result is True
