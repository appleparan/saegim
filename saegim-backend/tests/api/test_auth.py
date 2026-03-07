"""Tests for authentication endpoints."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import hash_password


class TestRegisterEndpoint:
    """Test cases for POST /auth/register."""

    def test_first_user_becomes_admin(self, client: TestClient):
        user_id = uuid.uuid4()
        record = {
            'id': user_id,
            'name': 'Admin',
            'email': 'admin@example.com',
            'role': 'admin',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with (
            patch(
                'saegim.repositories.user_repo.count_all',
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                'saegim.repositories.user_repo.create_with_password',
                new_callable=AsyncMock,
                return_value=record,
            ) as mock_create,
        ):
            response = client.post(
                '/api/v1/auth/register',
                json={
                    'name': 'Admin',
                    'email': 'admin@example.com',
                    'password': 'password123',
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        # Verify admin role was passed
        assert mock_create.call_args.kwargs['role'] == 'admin'

    def test_subsequent_user_becomes_annotator(self, client: TestClient):
        user_id = uuid.uuid4()
        record = {
            'id': user_id,
            'name': 'User',
            'email': 'user@example.com',
            'role': 'annotator',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with (
            patch(
                'saegim.repositories.user_repo.count_all',
                new_callable=AsyncMock,
                return_value=3,
            ),
            patch(
                'saegim.repositories.user_repo.create_with_password',
                new_callable=AsyncMock,
                return_value=record,
            ) as mock_create,
        ):
            response = client.post(
                '/api/v1/auth/register',
                json={
                    'name': 'User',
                    'email': 'user@example.com',
                    'password': 'password123',
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert mock_create.call_args.kwargs['role'] == 'annotator'

    def test_duplicate_email_returns_409(self, client: TestClient):
        with (
            patch(
                'saegim.repositories.user_repo.count_all',
                new_callable=AsyncMock,
                return_value=1,
            ),
            patch(
                'saegim.repositories.user_repo.create_with_password',
                new_callable=AsyncMock,
                side_effect=Exception('unique constraint violated'),
            ),
        ):
            response = client.post(
                '/api/v1/auth/register',
                json={
                    'name': 'Test',
                    'email': 'dup@example.com',
                    'password': 'password123',
                },
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_short_password_returns_422(self, client: TestClient):
        response = client.post(
            '/api/v1/auth/register',
            json={
                'name': 'Test',
                'email': 'test@example.com',
                'password': 'short',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Test cases for POST /auth/login."""

    def test_valid_login(self, client: TestClient):
        hashed = hash_password('password123')
        user_record = {
            'id': uuid.uuid4(),
            'name': 'Test',
            'email': 'test@example.com',
            'role': 'annotator',
            'password_hash': hashed,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test@example.com', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'

    def test_wrong_password_returns_401(self, client: TestClient):
        hashed = hash_password('correctpassword')
        user_record = {
            'id': uuid.uuid4(),
            'name': 'Test',
            'email': 'test@example.com',
            'role': 'annotator',
            'password_hash': hashed,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'test@example.com', 'password': 'wrongpassword'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_returns_401(self, client: TestClient):
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'nobody@example.com', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_without_password_returns_401(self, client: TestClient):
        user_record = {
            'id': uuid.uuid4(),
            'name': 'Legacy',
            'email': 'legacy@example.com',
            'role': 'annotator',
            'password_hash': None,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'email': 'legacy@example.com', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_same_error_message_for_all_failures(self, client: TestClient):
        """Ensure we don't leak email existence info."""
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value=None,
        ):
            r1 = client.post(
                '/api/v1/auth/login',
                json={'email': 'nobody@example.com', 'password': 'pass12345'},
            )

        hashed = hash_password('correct')
        with patch(
            'saegim.repositories.user_repo.get_by_email',
            new_callable=AsyncMock,
            return_value={
                'id': uuid.uuid4(),
                'name': 'X',
                'email': 'x@example.com',
                'role': 'annotator',
                'password_hash': hashed,
                'created_at': datetime.datetime.now(tz=datetime.UTC),
            },
        ):
            r2 = client.post(
                '/api/v1/auth/login',
                json={'email': 'x@example.com', 'password': 'wrongpass'},
            )

        assert r1.json()['detail'] == r2.json()['detail']
