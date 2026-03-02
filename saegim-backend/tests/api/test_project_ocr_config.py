"""Tests for project OCR config endpoints (legacy format, to be rewritten in Stage 3)."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


def _new_fmt(engines: dict | None = None, default_id: str | None = None) -> dict:
    """Build a new-format OCR config (multi-instance) for mock returns."""
    return {
        'default_engine_id': default_id,
        'engines': engines or {},
    }


class TestGetOcrConfig:
    """Test GET /projects/{id}/ocr-config (legacy response format)."""

    def test_get_default_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'pdfminer'

    def test_get_existing_commercial_api_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={
                'commercial-api': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini API',
                    'config': {
                        'provider': 'gemini',
                        'api_key': 'test-key',
                        'model': 'gemini-3-flash-preview',
                    },
                },
            },
            default_id='commercial-api',
        )
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
    """Test PUT /projects/{id}/ocr-config (legacy format)."""

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

    def test_update_vllm(self, client: TestClient, sample_project_record):
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
                    'engine_type': 'vllm',
                    'vllm': {
                        'host': 'localhost',
                        'port': 8000,
                        'model': 'datalab-to/chandra',
                    },
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'vllm'
        assert data['vllm']['host'] == 'localhost'
        assert data['vllm']['port'] == 8000
        assert data['vllm']['model'] == 'datalab-to/chandra'

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
                        'docling_model_name': 'ibm-granite/granite-docling-258M',
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

    def test_update_vllm_without_sub_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={'engine_type': 'vllm'},
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

    def test_update_with_enabled_engines(self, client: TestClient, sample_project_record):
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
                    'vllm': {
                        'host': 'localhost',
                        'port': 8000,
                        'model': 'datalab-to/chandra',
                    },
                    'enabled_engines': ['commercial_api', 'vllm'],
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['engine_type'] == 'commercial_api'
        assert set(data['enabled_engines']) == {'commercial_api', 'vllm'}

    def test_update_enabled_engines_without_sub_config_fails(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        response = client.put(
            f'/api/v1/projects/{project_id}/ocr-config',
            json={
                'engine_type': 'pdfminer',
                'enabled_engines': ['pdfminer', 'vllm'],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_enabled_engines_with_pdfminer_only(
        self,
        client: TestClient,
        sample_project_record,
    ):
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
                    'engine_type': 'pdfminer',
                    'enabled_engines': ['pdfminer'],
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['enabled_engines'] == ['pdfminer']

    def test_update_empty_enabled_engines(
        self,
        client: TestClient,
        sample_project_record,
    ):
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
                    'engine_type': 'pdfminer',
                    'enabled_engines': [],
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['enabled_engines'] == []


class TestGetAvailableEngines:
    """Test GET /projects/{id}/available-engines (legacy format)."""

    def test_returns_engines_from_config(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={
                'commercial-api': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini API',
                    'config': {'provider': 'gemini', 'api_key': 'test-key'},
                },
                'vllm': {
                    'engine_type': 'vllm',
                    'name': 'vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
            },
            default_id='commercial-api',
        )
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        engine_types = [e['engine_type'] for e in data['engines']]
        assert 'commercial_api' in engine_types
        assert 'vllm' in engine_types

    def test_empty_when_no_engines(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engines'] == []

    def test_returns_correct_labels(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={
                'split-pipeline': {
                    'engine_type': 'split_pipeline',
                    'name': 'Docling + OCR',
                    'config': {
                        'docling_model_name': 'ibm-granite/granite-docling-258M',
                        'ocr_provider': 'gemini',
                        'ocr_api_key': 'test-key',
                    },
                },
                'vllm': {
                    'engine_type': 'vllm',
                    'name': 'vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
            },
            default_id='split-pipeline',
        )
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        engines = {e['engine_type']: e['label'] for e in response.json()['engines']}
        assert engines['split_pipeline'] == 'Docling + OCR'
        assert engines['vllm'] == 'vLLM'

    def test_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get(
                '/api/v1/projects/00000000-0000-0000-0000-000000000000/available-engines'
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_config_returns_empty_engines(
        self,
        client: TestClient,
        sample_project_record,
    ):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engines'] == []
