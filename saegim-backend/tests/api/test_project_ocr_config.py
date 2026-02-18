"""Tests for project OCR config endpoints (2-stage pipeline)."""

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
        assert data['layout_provider'] == 'pymupdf'

    def test_get_legacy_config_falls_back_to_pymupdf(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        legacy_config = {'provider': 'gemini', 'gemini': {'api_key': 'k'}}
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=legacy_config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['layout_provider'] == 'pymupdf'

    def test_get_existing_ppstructure_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        config = {
            'layout_provider': 'ppstructure',
            'ocr_provider': 'gemini',
            'ppstructure': {'host': 'localhost', 'port': 18811},
            'gemini': {'api_key': 'test-key', 'model': 'gemini-2.0-flash'},
        }
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['layout_provider'] == 'ppstructure'
        assert data['ocr_provider'] == 'gemini'
        assert data['gemini']['api_key'] == 'test-key'

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

    def test_update_pymupdf_config(self, client: TestClient, sample_project_record):
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
                json={'layout_provider': 'pymupdf'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['layout_provider'] == 'pymupdf'

    def test_update_ppstructure_gemini(self, client: TestClient, sample_project_record):
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
                    'layout_provider': 'ppstructure',
                    'ocr_provider': 'gemini',
                    'ppstructure': {'host': 'localhost', 'port': 18811},
                    'gemini': {'api_key': 'my-key', 'model': 'gemini-2.0-flash'},
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['layout_provider'] == 'ppstructure'
        assert data['ocr_provider'] == 'gemini'
        assert data['gemini']['api_key'] == 'my-key'

    def test_update_ppstructure_olmocr(self, client: TestClient, sample_project_record):
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
                    'layout_provider': 'ppstructure',
                    'ocr_provider': 'olmocr',
                    'ppstructure': {'host': 'localhost', 'port': 18811},
                    'vllm': {
                        'host': '192.168.1.10',
                        'port': 8080,
                        'model': 'allenai/olmOCR-2-7B-1025',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['layout_provider'] == 'ppstructure'
        assert data['ocr_provider'] == 'olmocr'
        assert data['vllm']['host'] == '192.168.1.10'

    def test_update_ppstructure_ppocr(self, client: TestClient, sample_project_record):
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
                    'layout_provider': 'ppstructure',
                    'ocr_provider': 'ppocr',
                    'ppstructure': {'host': 'localhost', 'port': 18811},
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['layout_provider'] == 'ppstructure'
        assert data['ocr_provider'] == 'ppocr'

    def test_update_ppstructure_without_ppstructure_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ocr_provider': 'ppocr',
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_ppstructure_without_ocr_provider(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ppstructure': {'host': 'localhost', 'port': 18811},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_gemini_without_gemini_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ocr_provider': 'gemini',
                'ppstructure': {'host': 'localhost', 'port': 18811},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_olmocr_without_vllm_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ocr_provider': 'olmocr',
                'ppstructure': {'host': 'localhost', 'port': 18811},
            },
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
                json={'layout_provider': 'pymupdf'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_invalid_layout_provider(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'layout_provider': 'invalid_provider'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_gemini_empty_api_key(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ocr_provider': 'gemini',
                'ppstructure': {'host': 'localhost', 'port': 18811},
                'gemini': {'api_key': '', 'model': 'gemini-2.0-flash'},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_ppstructure_invalid_port(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'layout_provider': 'ppstructure',
                'ocr_provider': 'ppocr',
                'ppstructure': {'host': 'localhost', 'port': 99999},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
