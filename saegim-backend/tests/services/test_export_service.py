"""Tests for export service OmniDocBench JSON generation."""

import io
import json
import uuid
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from saegim.services import export_service
from saegim.services.export_service import _document_dir_name, sanitize_filename


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


class TestExportProject:
    @pytest.mark.asyncio
    async def test_returns_none_when_project_not_found(self, mock_pool, project_id):
        with patch.object(export_service, 'project_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await export_service.export_project(mock_pool, project_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_exports_empty_project(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Empty Project'}

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        assert result['project_name'] == 'Empty Project'
        assert result['total_pages'] == 0
        assert result['data'] == []

    @pytest.mark.asyncio
    async def test_exports_single_page(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test Project'}
        page = {
            'page_no': 1,
            'width': 1200,
            'height': 1600,
            'image_path': '/storage/images/p1.png',
            'annotation_data': {
                'layout_dets': [
                    {'anno_id': 0, 'category_type': 'text_block', 'text': 'Hello'},
                ],
                'page_attribute': {'language': 'ko', 'layout': 'single_column'},
                'extra': {'relation': []},
            },
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        assert result['project_name'] == 'Test Project'
        assert result['total_pages'] == 1
        assert len(result['data']) == 1

        entry = result['data'][0]
        assert 'page_info' in entry
        assert entry['page_info']['page_no'] == 1
        assert entry['page_info']['width'] == 1200
        assert entry['page_info']['height'] == 1600
        assert entry['page_info']['image_path'] == '/storage/images/p1.png'
        assert entry['page_info']['page_attribute'] == {
            'language': 'ko',
            'layout': 'single_column',
        }

    @pytest.mark.asyncio
    async def test_page_attribute_moved_to_page_info(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/img.png',
            'annotation_data': {
                'layout_dets': [],
                'page_attribute': {'language': 'en'},
                'extra': {},
            },
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        entry = result['data'][0]
        assert 'page_attribute' not in entry
        assert entry['page_info']['page_attribute'] == {'language': 'en'}

    @pytest.mark.asyncio
    async def test_layout_dets_preserved_in_export(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        elements = [
            {'anno_id': 0, 'category_type': 'text_block'},
            {'anno_id': 1, 'category_type': 'figure'},
        ]
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/img.png',
            'annotation_data': {
                'layout_dets': elements,
                'page_attribute': {},
            },
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        entry = result['data'][0]
        assert entry['layout_dets'] == elements

    @pytest.mark.asyncio
    async def test_exports_multiple_pages(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Multi'}
        pages = [
            {
                'page_no': i,
                'width': 800,
                'height': 1000,
                'image_path': f'/img_{i}.png',
                'annotation_data': {'layout_dets': [], 'page_attribute': {}},
            }
            for i in range(1, 4)
        ]

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=pages)
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        assert result['total_pages'] == 3
        for i, entry in enumerate(result['data'], start=1):
            assert entry['page_info']['page_no'] == i

    @pytest.mark.asyncio
    async def test_handles_json_string_annotation(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/img.png',
            'annotation_data': '{"layout_dets": [], "page_attribute": {"language": "ko"}}',
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        entry = result['data'][0]
        assert entry['layout_dets'] == []
        assert entry['page_info']['page_attribute'] == {'language': 'ko'}

    @pytest.mark.asyncio
    async def test_handles_null_annotation_data(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/img.png',
            'annotation_data': None,
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        entry = result['data'][0]
        assert entry['page_info']['page_attribute'] == {}

    @pytest.mark.asyncio
    async def test_extra_field_preserved(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/img.png',
            'annotation_data': {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': [{'src': 0, 'dst': 1}]},
            },
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project = AsyncMock(return_value=[page])
            result = await export_service.export_project(mock_pool, project_id)

        assert result is not None
        entry = result['data'][0]
        assert entry['extra'] == {'relation': [{'src': 0, 'dst': 1}]}


class TestSanitizeFilename:
    def test_replaces_whitespace(self):
        assert sanitize_filename('hello world') == 'hello_world'

    def test_removes_unsafe_characters(self):
        assert sanitize_filename('file<>:"/\\|?*name') == 'filename'

    def test_strips_leading_trailing_dots_underscores(self):
        assert sanitize_filename('..._name_...') == 'name'

    def test_preserves_unicode(self):
        assert sanitize_filename('논문_레이블링') == '논문_레이블링'

    def test_returns_export_for_empty_result(self):
        assert sanitize_filename('***') == 'export'

    def test_multiple_spaces_become_single_underscore(self):
        assert sanitize_filename('a   b') == 'a_b'

    def test_tabs_and_newlines(self):
        assert sanitize_filename('a\tb\nc') == 'a_b_c'


class TestDocumentDirName:
    def test_removes_pdf_extension(self):
        assert _document_dir_name('paper.pdf') == 'paper'

    def test_removes_any_extension(self):
        assert _document_dir_name('document.PDF') == 'document'

    def test_sanitizes_result(self):
        assert _document_dir_name('my paper?.pdf') == 'my_paper'

    def test_handles_no_extension(self):
        assert _document_dir_name('paper') == 'paper'


class TestExportProjectZip:
    @pytest.mark.asyncio
    async def test_returns_none_when_project_not_found(self, mock_pool, project_id):
        with patch.object(export_service, 'project_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await export_service.export_project_zip(mock_pool, project_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_zip_bytes_and_filename(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test Project'}

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project_with_document = AsyncMock(return_value=[])
            result = await export_service.export_project_zip(mock_pool, project_id)

        assert result is not None
        zip_bytes, zip_filename = result
        assert isinstance(zip_bytes, bytes)
        assert zip_filename.startswith('Test_Project_')
        assert zip_filename.endswith('.zip')

    @pytest.mark.asyncio
    async def test_zip_contains_annos_json(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/nonexistent/p1.png',
            'annotation_data': {
                'layout_dets': [{'anno_id': 0, 'category_type': 'text_block'}],
                'page_attribute': {'language': 'ko'},
            },
            'document_filename': 'paper.pdf',
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project_with_document = AsyncMock(return_value=[page])
            result = await export_service.export_project_zip(mock_pool, project_id)

        zip_bytes, _ = result
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert 'annos.json' in zf.namelist()
            annos = json.loads(zf.read('annos.json'))
            assert annos['project_name'] == 'Test'
            assert annos['total_pages'] == 1
            entry = annos['data'][0]
            assert entry['page_info']['image_path'] == 'images/paper/page_001.png'
            assert entry['page_info']['page_attribute'] == {'language': 'ko'}

    @pytest.mark.asyncio
    async def test_zip_includes_existing_image(self, mock_pool, project_id, tmp_path):
        image_file = tmp_path / 'test_image.png'
        image_file.write_bytes(b'fake-png-data')

        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': str(image_file),
            'annotation_data': {'layout_dets': [], 'page_attribute': {}},
            'document_filename': 'doc.pdf',
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project_with_document = AsyncMock(return_value=[page])
            result = await export_service.export_project_zip(mock_pool, project_id)

        zip_bytes, _ = result
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert 'images/doc/page_001.png' in zf.namelist()
            assert zf.read('images/doc/page_001.png') == b'fake-png-data'

    @pytest.mark.asyncio
    async def test_zip_skips_missing_image(self, mock_pool, project_id):
        project = {'id': project_id, 'name': 'Test'}
        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': '/does/not/exist.png',
            'annotation_data': {'layout_dets': [], 'page_attribute': {}},
            'document_filename': 'doc.pdf',
        }

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project_with_document = AsyncMock(return_value=[page])
            result = await export_service.export_project_zip(mock_pool, project_id)

        zip_bytes, _ = result
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # Only annos.json, no image file
            assert zf.namelist() == ['annos.json']

    @pytest.mark.asyncio
    async def test_zip_multiple_documents(self, mock_pool, project_id, tmp_path):
        img1 = tmp_path / 'img1.png'
        img2 = tmp_path / 'img2.png'
        img1.write_bytes(b'img1')
        img2.write_bytes(b'img2')

        project = {'id': project_id, 'name': 'Multi'}
        pages = [
            {
                'page_no': 1,
                'width': 800,
                'height': 1000,
                'image_path': str(img1),
                'annotation_data': {'layout_dets': [], 'page_attribute': {}},
                'document_filename': 'paper_a.pdf',
            },
            {
                'page_no': 1,
                'width': 800,
                'height': 1000,
                'image_path': str(img2),
                'annotation_data': {'layout_dets': [], 'page_attribute': {}},
                'document_filename': 'paper_b.pdf',
            },
        ]

        with (
            patch.object(export_service, 'project_repo') as mock_proj,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_proj.get_by_id = AsyncMock(return_value=project)
            mock_page.get_all_by_project_with_document = AsyncMock(return_value=pages)
            result = await export_service.export_project_zip(mock_pool, project_id)

        zip_bytes, _ = result
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert 'images/paper_a/page_001.png' in names
            assert 'images/paper_b/page_001.png' in names
            assert 'annos.json' in names


class TestExportDocumentZip:
    @pytest.mark.asyncio
    async def test_returns_none_when_document_not_found(self, mock_pool, project_id):
        doc_id = uuid.uuid4()
        with patch.object(export_service, 'document_repo') as mock_doc:
            mock_doc.get_by_id = AsyncMock(return_value=None)
            result = await export_service.export_document_zip(mock_pool, project_id, doc_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_document_not_in_project(self, mock_pool, project_id):
        doc_id = uuid.uuid4()
        other_project = uuid.uuid4()
        doc = {'id': doc_id, 'project_id': other_project, 'filename': 'test.pdf'}

        with patch.object(export_service, 'document_repo') as mock_doc:
            mock_doc.get_by_id = AsyncMock(return_value=doc)
            result = await export_service.export_document_zip(mock_pool, project_id, doc_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_exports_document_zip(self, mock_pool, project_id, tmp_path):
        doc_id = uuid.uuid4()
        doc = {'id': doc_id, 'project_id': project_id, 'filename': 'report.pdf'}

        img = tmp_path / 'p1.png'
        img.write_bytes(b'image-data')

        page = {
            'page_no': 1,
            'width': 800,
            'height': 1000,
            'image_path': str(img),
            'annotation_data': {
                'layout_dets': [{'anno_id': 0, 'category_type': 'title'}],
                'page_attribute': {'language': 'en'},
            },
        }

        with (
            patch.object(export_service, 'document_repo') as mock_doc,
            patch.object(export_service, 'page_repo') as mock_page,
        ):
            mock_doc.get_by_id = AsyncMock(return_value=doc)
            mock_page.list_by_document_for_export = AsyncMock(return_value=[page])
            result = await export_service.export_document_zip(mock_pool, project_id, doc_id)

        assert result is not None
        zip_bytes, zip_filename = result
        assert zip_filename.startswith('report_')
        assert zip_filename.endswith('.zip')

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert 'images/report/page_001.png' in names
            assert 'annos.json' in names
            annos = json.loads(zf.read('annos.json'))
            assert annos['document_name'] == 'report.pdf'
            assert annos['total_pages'] == 1
