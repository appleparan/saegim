"""Tests for health check endpoints."""

from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint.

        Args:
            client: FastAPI test client.
        """
        response = client.get('/api/v1/health')

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data['status'] == 'healthy'
        assert data['message'] == 'saegim API is running'
        assert data['version'] == '0.1.0'

    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint.

        Args:
            client: FastAPI test client.
        """
        response = client.get('/api/v1/health/ready')

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data['status'] == 'ready'
        assert data['message'] == 'saegim API is ready to serve requests'
        assert data['version'] == '0.1.0'

    def test_health_endpoints_return_correct_content_type(self, client: TestClient):
        """Test that health endpoints return JSON content type.

        Args:
            client: FastAPI test client.
        """
        response = client.get('/api/v1/health')
        assert response.headers['content-type'] == 'application/json'

        response = client.get('/api/v1/health/ready')
        assert response.headers['content-type'] == 'application/json'
