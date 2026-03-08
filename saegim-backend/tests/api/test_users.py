"""Tests for user endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Test cases for user API endpoints."""

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

    def test_list_users_requires_auth(self, app, sample_user_record):
        from saegim.api.deps import get_current_user

        app.dependency_overrides.pop(get_current_user, None)
        unauthenticated_client = TestClient(app)
        response = unauthenticated_client.get('/api/v1/users')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
