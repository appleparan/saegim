"""Tests for user endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Test cases for user API endpoints."""

    def test_create_user(self, client: TestClient, sample_user_record):
        with patch(
            'saegim.repositories.user_repo.create',
            new_callable=AsyncMock,
            return_value=sample_user_record,
        ):
            response = client.post(
                '/api/v1/users',
                json={'name': 'Test User', 'email': 'test@example.com', 'role': 'annotator'},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == 'Test User'
        assert data['email'] == 'test@example.com'
        assert data['role'] == 'annotator'

    def test_create_user_invalid_email(self, client: TestClient):
        response = client.post(
            '/api/v1/users',
            json={'name': 'Test User', 'email': 'not-an-email', 'role': 'annotator'},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_invalid_role(self, client: TestClient):
        response = client.post(
            '/api/v1/users',
            json={'name': 'Test User', 'email': 'test@example.com', 'role': 'invalid'},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_users(self, client: TestClient, sample_user_record):
        with patch(
            'saegim.repositories.user_repo.list_all',
            new_callable=AsyncMock,
            return_value=[sample_user_record],
        ):
            response = client.get('/api/v1/users')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_list_users_empty(self, client: TestClient):
        with patch(
            'saegim.repositories.user_repo.list_all',
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = client.get('/api/v1/users')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_create_user_default_role(self, client: TestClient, sample_user_record):
        with patch(
            'saegim.repositories.user_repo.create',
            new_callable=AsyncMock,
            return_value=sample_user_record,
        ):
            response = client.post(
                '/api/v1/users',
                json={'name': 'Test User', 'email': 'test@example.com'},
            )

        assert response.status_code == status.HTTP_201_CREATED
