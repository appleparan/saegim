"""Tests for project endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestProjectEndpoints:
    """Test cases for project API endpoints."""

    def test_create_project(self, client: TestClient, sample_project_record):
        with patch(
            'saegim.repositories.project_repo.create',
            new_callable=AsyncMock,
            return_value=sample_project_record,
        ):
            response = client.post(
                '/api/v1/projects',
                json={'name': 'Test Project', 'description': 'A test project'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == 'Test Project'
        assert data['description'] == 'A test project'
        assert 'id' in data
        assert 'created_at' in data

    def test_create_project_missing_name(self, client: TestClient):
        response = client.post('/api/v1/projects', json={'description': 'no name'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_project_empty_name(self, client: TestClient):
        response = client.post('/api/v1/projects', json={'name': '', 'description': 'empty'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_projects(self, client: TestClient, sample_project_record):
        with patch(
            'saegim.repositories.project_repo.list_all',
            new_callable=AsyncMock,
            return_value=[sample_project_record],
        ):
            response = client.get('/api/v1/projects')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Test Project'

    def test_list_projects_empty(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.list_all',
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = client.get('/api/v1/projects')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_project(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=sample_project_record,
        ):
            response = client.get(f'/api/v1/projects/{project_id}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Test Project'

    def test_get_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get('/api/v1/projects/00000000-0000-0000-0000-000000000000')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_invalid_uuid(self, client: TestClient):
        response = client.get('/api/v1/projects/not-a-uuid')
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
