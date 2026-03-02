"""Tests for project OCR config endpoints (multi-instance format)."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


def _new_fmt(engines: dict | None = None, default_id: str | None = None) -> dict:
    """Build a multi-instance OCR config for mock returns."""
    return {
        'default_engine_id': default_id,
        'engines': engines or {},
    }


def _vllm_engine(name: str = 'My vLLM', host: str = 'localhost', port: int = 8000) -> dict:
    return {
        'engine_type': 'vllm',
        'name': name,
        'config': {'host': host, 'port': port, 'model': 'datalab-to/chandra'},
    }


def _gemini_engine(name: str = 'Gemini Flash') -> dict:
    return {
        'engine_type': 'commercial_api',
        'name': name,
        'config': {'provider': 'gemini', 'api_key': 'test-key', 'model': 'gemini-3-flash-preview'},
    }


class TestGetOcrConfig:
    def test_get_empty_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['default_engine_id'] is None
        assert data['engines'] == {}

    def test_get_config_with_engines(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={'gemini-flash': _gemini_engine(), 'my-vllm': _vllm_engine()},
            default_id='gemini-flash',
        )
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/ocr-config')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['default_engine_id'] == 'gemini-flash'
        assert 'gemini-flash' in data['engines']
        assert 'my-vllm' in data['engines']
        assert data['engines']['gemini-flash']['engine_type'] == 'commercial_api'

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


class TestAddEngine:
    def test_add_first_engine(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=_new_fmt(),
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/ocr-config/engines',
                json={
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'gpu-server', 'port': 8000, 'model': 'test'},
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'my-vllm' in data['engines']
        assert data['default_engine_id'] == 'my-vllm'

    def test_add_engine_with_custom_id(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=_new_fmt(),
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/ocr-config/engines',
                json={
                    'engine_id': 'custom-id',
                    'engine_type': 'vllm',
                    'name': 'Custom vLLM',
                    'config': {'host': 'h', 'port': 8000},
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert 'custom-id' in response.json()['engines']

    def test_add_engine_duplicate_id_conflict(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/ocr-config/engines',
                json={
                    'engine_id': 'my-vllm',
                    'engine_type': 'vllm',
                    'name': 'Duplicate',
                    'config': {'host': 'h', 'port': 8000},
                },
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_add_engine_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post(
                '/api/v1/projects/00000000-0000-0000-0000-000000000000/ocr-config/engines',
                json={
                    'engine_type': 'vllm',
                    'name': 'test',
                    'config': {'host': 'h', 'port': 8000},
                },
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateEngine:
    def test_update_engine_name(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/engines/my-vllm',
                json={'name': 'Updated vLLM'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engines']['my-vllm']['name'] == 'Updated vLLM'

    def test_update_engine_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/engines/my-vllm',
                json={'config': {'host': 'new-host', 'port': 9000, 'model': 'new-model'}},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engines']['my-vllm']['config']['host'] == 'new-host'

    def test_update_engine_not_found(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt()
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/engines/nonexistent',
                json={'name': 'New Name'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEngine:
    def test_delete_engine(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={'my-vllm': _vllm_engine(), 'gemini': _gemini_engine()},
            default_id='my-vllm',
        )
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/ocr-config/engines/gemini',
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'gemini' not in data['engines']
        assert 'my-vllm' in data['engines']
        assert data['default_engine_id'] == 'my-vllm'

    def test_delete_default_engine_clears_default(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/ocr-config/engines/my-vllm',
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['default_engine_id'] is None
        assert data['engines'] == {}

    def test_delete_engine_not_found(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/ocr-config/engines/nonexistent',
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSetDefaultEngine:
    def test_set_default_engine(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={'my-vllm': _vllm_engine(), 'gemini': _gemini_engine()},
            default_id='my-vllm',
        )
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/default-engine',
                json={'engine_id': 'gemini'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['default_engine_id'] == 'gemini'

    def test_clear_default_engine(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.repositories.project_repo.update_ocr_config',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/default-engine',
                json={'engine_id': None},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['default_engine_id'] is None

    def test_set_default_to_nonexistent_engine(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.put(
                f'/api/v1/projects/{project_id}/ocr-config/default-engine',
                json={'engine_id': 'nonexistent'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTestEngineConnection:
    def test_test_connection_success(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(engines={'my-vllm': _vllm_engine()}, default_id='my-vllm')
        with (
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=config,
            ),
            patch(
                'saegim.services.engines.factory._build_engine_from_type',
            ) as mock_build,
        ):
            mock_engine = mock_build.return_value
            mock_engine.test_connection.return_value = (True, 'Connected')

            response = client.post(
                f'/api/v1/projects/{project_id}/ocr-config/test',
                json={'engine_id': 'my-vllm'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['success'] is True
        assert data['message'] == 'Connected'

    def test_test_connection_engine_not_found(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt()
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/ocr-config/test',
                json={'engine_id': 'nonexistent'},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetAvailableEngines:
    def test_returns_engines_from_config(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={'gemini-flash': _gemini_engine(), 'my-vllm': _vllm_engine()},
            default_id='gemini-flash',
        )
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        engine_ids = [e['engine_id'] for e in data['engines']]
        assert 'gemini-flash' in engine_ids
        assert 'my-vllm' in engine_ids

    def test_empty_when_no_engines(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=_new_fmt(),
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['engines'] == []

    def test_includes_engine_names(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        config = _new_fmt(
            engines={'my-vllm': _vllm_engine(name='GPU Server A')},
            default_id='my-vllm',
        )
        with patch(
            'saegim.repositories.project_repo.get_ocr_config',
            new_callable=AsyncMock,
            return_value=config,
        ):
            response = client.get(f'/api/v1/projects/{project_id}/available-engines')

        assert response.status_code == status.HTTP_200_OK
        engines = response.json()['engines']
        assert engines[0]['name'] == 'GPU Server A'
        assert engines[0]['engine_id'] == 'my-vllm'

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
