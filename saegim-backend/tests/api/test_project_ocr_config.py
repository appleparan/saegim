"""Tests for project OCR config endpoints (engine_type based)."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestGetOcrConfig:
    """Test GET /projects/{id}/ocr-config."""

    def test_get_default_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value={},
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'pdfminer'

    def test_get_config_without_engine_type_falls_back_to_pdfminer(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        stale_config = {'some_old_key': 'value'}
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=stale_config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engine_type'] == 'pdfminer'

    def test_get_existing_commercial_api_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        }
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'commercial_api'
        assert data['commercial_api']['provider'] == 'gemini'
        assert data['commercial_api']['api_key'] == 'test-key'

    def test_get_config_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get(
                '/api/v1/projects/00000000-0000-0000-0000-000000000000/ocr-config'
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateOcrConfig:
    """Test PUT /projects/{id}/ocr-config."""

    def test_update_pdfminer_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={'engine_type': 'pdfminer'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engine_type'] == 'pdfminer'

    def test_update_commercial_api_gemini(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={
                    'engine_type': 'commercial_api',
                    'commercial_api': {
                        'provider': 'gemini',
                        'api_key': 'my-key',
                        'model': 'gemini-3-flash-preview',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'commercial_api'
        assert data['commercial_api']['provider'] == 'gemini'
        assert data['commercial_api']['api_key'] == 'my-key'

    def test_update_integrated_server(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={
                    'engine_type': 'integrated_server',
                    'integrated_server': {
                        'host': 'localhost',
                        'port': 8000,
                        'model': 'datalab-to/chandra',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'integrated_server'
        assert data['integrated_server']['host'] == 'localhost'
        assert data['integrated_server']['port'] == 8000
        assert data['integrated_server']['model'] == 'datalab-to/chandra'

    def test_update_split_pipeline_gemini(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={
                    'engine_type': 'split_pipeline',
                    'split_pipeline': {
                        'layout_server_url': 'http://localhost:18811',
                        'ocr_provider': 'gemini',
                        'ocr_api_key': 'my-key',
                        'ocr_model': 'gemini-3-flash-preview',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'split_pipeline'
        assert data['split_pipeline']['ocr_provider'] == 'gemini'

    def test_update_commercial_api_without_sub_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'engine_type': 'commercial_api'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_integrated_server_without_sub_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'engine_type': 'integrated_server'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_split_pipeline_without_sub_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'engine_type': 'split_pipeline'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_config_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.put(
                '/api/v1/projects/00000000-0000-0000-0000-000000000000/ocr-config',
                json={'engine_type': 'pdfminer'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_docling_default(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={'engine_type': 'docling'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engine_type'] == 'docling'

    def test_update_docling_custom_model(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_project_record,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config',
                json={
                    'engine_type': 'docling',
                    'docling': {'model_name': 'custom/model'},
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'docling'
        assert data['docling']['model_name'] == 'custom/model'

    def test_update_invalid_engine_type(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'engine_type': 'invalid_engine'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
