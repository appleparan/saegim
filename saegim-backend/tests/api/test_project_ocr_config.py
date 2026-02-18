"""Tests for project OCR config endpoints."""

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
        assert data['provider'] == 'pymupdf'

    def test_get_existing_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = {
            'provider': 'gemini',
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
        assert data['provider'] == 'gemini'
        assert data['gemini']['api_key'] == 'test-key'
        assert data['gemini']['model'] == 'gemini-2.0-flash'

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

    def test_update_gemini_config(self, client: TestClient, sample_project_record):
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
                    'provider': 'gemini',
                    'gemini': {'api_key': 'my-key', 'model': 'gemini-2.0-flash'},
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['provider'] == 'gemini'
        assert data['gemini']['api_key'] == 'my-key'

    def test_update_vllm_config(self, client: TestClient, sample_project_record):
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
                    'provider': 'vllm',
                    'vllm': {
                        'host': '192.168.1.10',
                        'port': 8080,
                        'model': 'Qwen/Qwen2.5-VL-72B-Instruct',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['provider'] == 'vllm'
        assert data['vllm']['host'] == '192.168.1.10'
        assert data['vllm']['port'] == 8080

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
                json={'provider': 'pymupdf'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['provider'] == 'pymupdf'

    def test_update_gemini_without_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'provider': 'gemini'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_vllm_without_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'provider': 'vllm'},
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
                json={'provider': 'pymupdf'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_invalid_provider(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'provider': 'invalid_provider'},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_gemini_empty_api_key(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'provider': 'gemini',
                'gemini': {'api_key': '', 'model': 'gemini-2.0-flash'},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_vllm_invalid_port(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'provider': 'vllm',
                'vllm': {'host': 'localhost', 'port': 99999, 'model': 'test'},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
