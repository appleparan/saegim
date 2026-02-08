"""Tests for page labeling endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestPageEndpoints:
    """Test cases for page labeling API endpoints."""

    def test_get_page(self, client: TestClient, sample_page_record):
        page_id = sample_page_record['id']
        with patch(
            'saegim.services.labeling_service.get_page_data',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.get(f'/api/v1/pages/{page_id}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['page_no'] == 1
        assert data['width'] == 1200
        assert data['height'] == 1600
        assert 'annotation_data' in data
        assert 'layout_dets' in data['annotation_data']

    def test_get_page_not_found(self, client: TestClient):
        with patch(
            'saegim.services.labeling_service.get_page_data',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get('/api/v1/pages/00000000-0000-0000-0000-000000000000')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_annotation(self, client: TestClient, sample_page_record):
        page_id = sample_page_record['id']
        annotation = {
            'layout_dets': [],
            'page_attribute': {'language': 'ko'},
            'extra': {'relation': []},
        }
        with patch(
            'saegim.services.labeling_service.save_annotation',
            new_callable=AsyncMock,
            return_value={**sample_page_record, 'annotation_data': annotation},
        ):
            response = client.put(
                f'/api/v1/pages/{page_id}',
                json={'annotation_data': annotation},
            )

        assert response.status_code == status.HTTP_200_OK

    def test_update_annotation_not_found(self, client: TestClient):
        with patch(
            'saegim.services.labeling_service.save_annotation',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.put(
                '/api/v1/pages/00000000-0000-0000-0000-000000000000',
                json={'annotation_data': {}},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_page_attributes(self, client: TestClient, sample_page_record):
        page_id = sample_page_record['id']
        with patch(
            'saegim.services.labeling_service.save_page_attribute',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.put(
                f'/api/v1/pages/{page_id}/attributes',
                json={'page_attribute': {'language': 'ko', 'layout': 'single_column'}},
            )

        assert response.status_code == status.HTTP_200_OK

    def test_add_element(self, client: TestClient, sample_page_record):
        page_id = sample_page_record['id']
        with patch(
            'saegim.services.labeling_service.add_element',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/elements',
                json={
                    'category_type': 'text_block',
                    'poly': [100, 200, 300, 200, 300, 400, 100, 400],
                    'text': 'New element',
                },
            )

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_element_invalid_poly(self, client: TestClient):
        response = client.post(
            '/api/v1/pages/00000000-0000-0000-0000-000000000000/elements',
            json={
                'category_type': 'text_block',
                'poly': [100, 200],
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_element(self, client: TestClient, sample_page_record):
        page_id = sample_page_record['id']
        with patch(
            'saegim.services.labeling_service.delete_element',
            new_callable=AsyncMock,
            return_value=sample_page_record,
        ):
            response = client.delete(f'/api/v1/pages/{page_id}/elements/0')

        assert response.status_code == status.HTTP_200_OK

    def test_delete_element_not_found(self, client: TestClient):
        with patch(
            'saegim.services.labeling_service.delete_element',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.delete(
                '/api/v1/pages/00000000-0000-0000-0000-000000000000/elements/99'
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
