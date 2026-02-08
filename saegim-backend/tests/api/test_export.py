"""Tests for export endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestExportEndpoints:
    """Test cases for export API endpoints."""

    def test_export_project(self, client: TestClient):
        export_data = {
            'project_name': 'Test Project',
            'total_pages': 2,
            'data': [
                {
                    'layout_dets': [],
                    'page_info': {
                        'page_no': 1,
                        'height': 1600,
                        'width': 1200,
                        'image_path': '/storage/images/p1.png',
                        'page_attribute': {'language': 'ko'},
                    },
                },
                {
                    'layout_dets': [],
                    'page_info': {
                        'page_no': 2,
                        'height': 1600,
                        'width': 1200,
                        'image_path': '/storage/images/p2.png',
                        'page_attribute': {'language': 'ko'},
                    },
                },
            ],
        }
        with patch(
            'saegim.services.export_service.export_project',
            new_callable=AsyncMock,
            return_value=export_data,
        ):
            response = client.post('/api/v1/projects/00000000-0000-0000-0000-000000000001/export')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['project_name'] == 'Test Project'
        assert data['total_pages'] == 2
        assert len(data['data']) == 2

    def test_export_project_not_found(self, client: TestClient):
        with patch(
            'saegim.services.export_service.export_project',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post('/api/v1/projects/00000000-0000-0000-0000-000000000000/export')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_export_response_structure(self, client: TestClient):
        export_data = {
            'project_name': 'Test',
            'total_pages': 1,
            'data': [
                {
                    'layout_dets': [
                        {
                            'category_type': 'text_block',
                            'poly': [0, 0, 100, 0, 100, 50, 0, 50],
                            'anno_id': 0,
                            'order': 0,
                            'text': 'hello',
                        },
                    ],
                    'page_info': {
                        'page_no': 1,
                        'height': 800,
                        'width': 600,
                        'image_path': '/img.png',
                        'page_attribute': {
                            'data_source': 'academic_literature',
                            'language': 'ko',
                        },
                    },
                    'extra': {'relation': []},
                },
            ],
        }
        with patch(
            'saegim.services.export_service.export_project',
            new_callable=AsyncMock,
            return_value=export_data,
        ):
            response = client.post('/api/v1/projects/00000000-0000-0000-0000-000000000001/export')

        data = response.json()
        page = data['data'][0]
        assert 'page_info' in page
        assert 'layout_dets' in page
        assert page['page_info']['page_attribute']['language'] == 'ko'
