"""Tests for export service OmniDocBench JSON generation."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from saegim.services import export_service


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
            'language': 'ko', 'layout': 'single_column',
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

        entry = result['data'][0]
        assert entry['extra'] == {'relation': [{'src': 0, 'dst': 1}]}
