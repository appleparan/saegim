"""Tests for labeling service annotation data management."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from saegim.services import labeling_service


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def page_id():
    return uuid.uuid4()


@pytest.fixture
def document_id():
    return uuid.uuid4()


def _make_page_record(
    page_id,
    document_id,
    *,
    annotation_data=None,
    auto_extracted_data=None,
    status='pending',
    with_context=False,
):
    record = {
        'id': page_id,
        'document_id': document_id,
        'page_no': 1,
        'width': 1200,
        'height': 1600,
        'image_path': '/storage/images/test_p1.png',
        'annotation_data': annotation_data,
        'auto_extracted_data': auto_extracted_data,
        'status': status,
        'assigned_to': None,
        'locked_at': None,
        'updated_at': datetime.datetime.now(tz=datetime.UTC),
    }
    if with_context:
        record['project_id'] = uuid.uuid4()
        record['project_name'] = 'Test Project'
        record['document_filename'] = 'test.pdf'
        record['pdf_path'] = '/storage/pdfs/test.pdf'
    return record


class TestGetPageData:
    @pytest.mark.asyncio
    async def test_returns_none_when_page_not_found(self, mock_pool, page_id):
        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id_with_context = AsyncMock(return_value=None)
            result = await labeling_service.get_page_data(mock_pool, page_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_page_data_with_dict_annotation(self, mock_pool, page_id, document_id):
        annotation = {'layout_dets': [], 'page_attribute': {'language': 'ko'}}
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data=annotation,
            with_context=True,
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id_with_context = AsyncMock(return_value=record)
            result = await labeling_service.get_page_data(mock_pool, page_id)

        assert result is not None
        assert result['id'] == page_id
        assert result['page_no'] == 1
        assert result['annotation_data'] == annotation
        assert result['auto_extracted_data'] is None

    @pytest.mark.asyncio
    async def test_parses_json_string_annotation(self, mock_pool, page_id, document_id):
        annotation_str = '{"layout_dets": [{"anno_id": 0}]}'
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data=annotation_str,
            with_context=True,
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id_with_context = AsyncMock(return_value=record)
            result = await labeling_service.get_page_data(mock_pool, page_id)

        assert result is not None
        assert result['annotation_data'] == {'layout_dets': [{'anno_id': 0}]}

    @pytest.mark.asyncio
    async def test_parses_json_string_auto_extracted(self, mock_pool, page_id, document_id):
        auto_data_str = '{"model": "test", "results": []}'
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data=None,
            auto_extracted_data=auto_data_str,
            with_context=True,
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id_with_context = AsyncMock(return_value=record)
            result = await labeling_service.get_page_data(mock_pool, page_id)

        assert result is not None
        assert result['auto_extracted_data'] == {'model': 'test', 'results': []}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_null_annotation(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data=None,
            with_context=True,
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id_with_context = AsyncMock(return_value=record)
            result = await labeling_service.get_page_data(mock_pool, page_id)

        assert result is not None
        assert result['annotation_data'] == {}


class TestSaveAnnotation:
    @pytest.mark.asyncio
    async def test_returns_none_when_page_not_found(self, mock_pool, page_id):
        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_annotation = AsyncMock(return_value=None)
            result = await labeling_service.save_annotation(mock_pool, page_id, {})

        assert result is None

    @pytest.mark.asyncio
    async def test_saves_and_returns_updated_annotation(self, mock_pool, page_id, document_id):
        annotation = {'layout_dets': [{'anno_id': 0, 'text': 'hello'}]}
        record = _make_page_record(page_id, document_id, annotation_data=annotation)

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_annotation = AsyncMock(return_value=record)
            result = await labeling_service.save_annotation(mock_pool, page_id, annotation)

        mock_repo.update_annotation.assert_called_once_with(mock_pool, page_id, annotation)
        assert result is not None
        assert result['annotation_data'] == annotation

    @pytest.mark.asyncio
    async def test_parses_json_string_result(self, mock_pool, page_id, document_id):
        annotation_str = '{"layout_dets": []}'
        record = _make_page_record(page_id, document_id, annotation_data=annotation_str)

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_annotation = AsyncMock(return_value=record)
            result = await labeling_service.save_annotation(mock_pool, page_id, {})

        assert result is not None
        assert result['annotation_data'] == {'layout_dets': []}


class TestSavePageAttribute:
    @pytest.mark.asyncio
    async def test_returns_none_when_page_not_found(self, mock_pool, page_id):
        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_page_attribute = AsyncMock(return_value=None)
            result = await labeling_service.save_page_attribute(mock_pool, page_id, {})

        assert result is None

    @pytest.mark.asyncio
    async def test_saves_page_attribute(self, mock_pool, page_id, document_id):
        page_attr = {'language': 'ko', 'layout': 'single_column'}
        annotation = {'layout_dets': [], 'page_attribute': page_attr}
        record = _make_page_record(page_id, document_id, annotation_data=annotation)

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_page_attribute = AsyncMock(return_value=record)
            result = await labeling_service.save_page_attribute(mock_pool, page_id, page_attr)

        mock_repo.update_page_attribute.assert_called_once_with(mock_pool, page_id, page_attr)
        assert result is not None
        assert result['annotation_data']['page_attribute'] == page_attr

    @pytest.mark.asyncio
    async def test_returns_all_page_fields(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data={'page_attribute': {'language': 'en'}},
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.update_page_attribute = AsyncMock(return_value=record)
            result = await labeling_service.save_page_attribute(mock_pool, page_id, {})

        assert result is not None
        assert result['id'] == page_id
        assert result['document_id'] == document_id
        assert result['page_no'] == 1
        assert result['width'] == 1200
        assert result['height'] == 1600
        assert result['image_path'] == '/storage/images/test_p1.png'
        assert result['status'] == 'pending'


class TestAddElement:
    @pytest.mark.asyncio
    async def test_returns_none_when_page_not_found(self, mock_pool, page_id):
        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await labeling_service.add_element(
                mock_pool,
                page_id,
                {'category_type': 'text_block'},
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_assigns_anno_id_starting_from_zero(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data={'layout_dets': []},
        )
        updated = _make_page_record(
            page_id,
            document_id,
            annotation_data={'layout_dets': [{'anno_id': 0, 'category_type': 'text_block'}]},
        )

        element = {'category_type': 'text_block', 'poly': [0, 0, 100, 0, 100, 100, 0, 100]}

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=record)
            mock_repo.add_element = AsyncMock(return_value=updated)
            await labeling_service.add_element(mock_pool, page_id, element)

        added = mock_repo.add_element.call_args[0][2]
        assert added['anno_id'] == 0
        assert added['order'] == 0

    @pytest.mark.asyncio
    async def test_assigns_next_anno_id(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data={
                'layout_dets': [
                    {'anno_id': 0, 'category_type': 'text_block'},
                    {'anno_id': 2, 'category_type': 'figure'},
                ],
            },
        )
        updated = _make_page_record(page_id, document_id, annotation_data={'layout_dets': []})

        element = {'category_type': 'table', 'poly': [0, 0, 100, 0, 100, 100, 0, 100]}

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=record)
            mock_repo.add_element = AsyncMock(return_value=updated)
            await labeling_service.add_element(mock_pool, page_id, element)

        added = mock_repo.add_element.call_args[0][2]
        assert added['anno_id'] == 3
        assert added['order'] == 2

    @pytest.mark.asyncio
    async def test_handles_null_annotation_data(self, mock_pool, page_id, document_id):
        record = _make_page_record(page_id, document_id, annotation_data=None)
        updated = _make_page_record(page_id, document_id, annotation_data={'layout_dets': []})

        element = {'category_type': 'text_block'}

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=record)
            mock_repo.add_element = AsyncMock(return_value=updated)
            await labeling_service.add_element(mock_pool, page_id, element)

        added = mock_repo.add_element.call_args[0][2]
        assert added['anno_id'] == 0
        assert added['order'] == 0

    @pytest.mark.asyncio
    async def test_handles_json_string_annotation(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data='{"layout_dets": [{"anno_id": 5}]}',
        )
        updated = _make_page_record(page_id, document_id, annotation_data={'layout_dets': []})

        element = {'category_type': 'figure'}

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=record)
            mock_repo.add_element = AsyncMock(return_value=updated)
            await labeling_service.add_element(mock_pool, page_id, element)

        added = mock_repo.add_element.call_args[0][2]
        assert added['anno_id'] == 6
        assert added['order'] == 1

    @pytest.mark.asyncio
    async def test_returns_none_when_add_element_fails(self, mock_pool, page_id, document_id):
        record = _make_page_record(page_id, document_id, annotation_data={'layout_dets': []})

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=record)
            mock_repo.add_element = AsyncMock(return_value=None)
            result = await labeling_service.add_element(
                mock_pool,
                page_id,
                {'category_type': 'text_block'},
            )

        assert result is None


class TestDeleteElement:
    @pytest.mark.asyncio
    async def test_returns_none_when_page_not_found(self, mock_pool, page_id):
        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.delete_element = AsyncMock(return_value=None)
            result = await labeling_service.delete_element(mock_pool, page_id, 0)

        assert result is None

    @pytest.mark.asyncio
    async def test_deletes_element_by_anno_id(self, mock_pool, page_id, document_id):
        remaining = {'layout_dets': [{'anno_id': 1, 'category_type': 'figure'}]}
        record = _make_page_record(page_id, document_id, annotation_data=remaining)

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.delete_element = AsyncMock(return_value=record)
            result = await labeling_service.delete_element(mock_pool, page_id, 0)

        mock_repo.delete_element.assert_called_once_with(mock_pool, page_id, 0)
        assert result is not None
        assert result['annotation_data'] == remaining

    @pytest.mark.asyncio
    async def test_parses_json_string_result(self, mock_pool, page_id, document_id):
        record = _make_page_record(
            page_id,
            document_id,
            annotation_data='{"layout_dets": []}',
        )

        with patch.object(labeling_service, 'page_repo') as mock_repo:
            mock_repo.delete_element = AsyncMock(return_value=record)
            result = await labeling_service.delete_element(mock_pool, page_id, 0)

        assert result is not None
        assert result['annotation_data'] == {'layout_dets': []}
