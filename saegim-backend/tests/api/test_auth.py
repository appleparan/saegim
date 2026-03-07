"""Tests for authentication endpoints."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import create_access_token, hash_password


class TestRegisterEndpoint:
    """Test cases for POST /auth/register."""

    def test_first_user_becomes_admin(self, client: TestClient):
        user_id = uuid.uuid4()
        record = {
            'id': user_id,
            'name': 'Admin',
            'login_id': 'admin',
            'email': 'admin@example.com',
            'role': 'admin',
            'must_change_password': False,
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
                    'login_id': 'admin',
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
            'login_id': 'user01',
            'email': 'user@example.com',
            'role': 'annotator',
            'must_change_password': False,
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
                    'login_id': 'user01',
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
                    'login_id': 'dup-user',
                    'password': 'password123',
                },
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_short_password_returns_422(self, client: TestClient):
        response = client.post(
            '/api/v1/auth/register',
            json={
                'name': 'Test',
                'login_id': 'testuser',
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
            'login_id': 'testuser',
            'email': 'test@example.com',
            'role': 'annotator',
            'password_hash': hashed,
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'testuser', 'password': 'password123'},
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
            'login_id': 'testuser',
            'email': 'test@example.com',
            'role': 'annotator',
            'password_hash': hashed,
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'testuser', 'password': 'wrongpassword'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_returns_401(self, client: TestClient):
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'nobody', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_without_password_returns_401(self, client: TestClient):
        user_record = {
            'id': uuid.uuid4(),
            'name': 'Legacy',
            'login_id': 'legacy',
            'email': 'legacy@example.com',
            'role': 'annotator',
            'password_hash': None,
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'legacy', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_same_error_message_for_all_failures(self, client: TestClient):
        """Ensure we don't leak email existence info."""
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            r1 = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'nobody', 'password': 'pass12345'},
            )

        hashed = hash_password('correct')
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value={
                'id': uuid.uuid4(),
                'name': 'X',
                'login_id': 'xuser',
                'email': 'x@example.com',
                'role': 'annotator',
                'password_hash': hashed,
                'must_change_password': False,
                'created_at': datetime.datetime.now(tz=datetime.UTC),
            },
        ):
            r2 = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'xuser', 'password': 'wrongpass'},
            )

        assert r1.json()['detail'] == r2.json()['detail']

    def test_login_returns_must_change_password_flag(self, client: TestClient):
        hashed = hash_password('password123')
        user_record = {
            'id': uuid.uuid4(),
            'name': 'Admin',
            'login_id': 'admin',
            'email': 'admin',
            'role': 'admin',
            'password_hash': hashed,
            'must_change_password': True,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_login_id',
            new_callable=AsyncMock,
            return_value=user_record,
        ):
            response = client.post(
                '/api/v1/auth/login',
                json={'login_id': 'admin', 'password': 'password123'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['must_change_password'] is True


class TestLoginIdCheckEndpoint:
    """Test cases for GET /auth/check-login-id."""

    def test_available(self, client: TestClient):
        with patch(
            'saegim.repositories.user_repo.is_login_id_taken',
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = client.get('/api/v1/auth/check-login-id?login_id=newuser')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'login_id': 'newuser', 'available': True}

    def test_unavailable(self, client: TestClient):
        with patch(
            'saegim.repositories.user_repo.is_login_id_taken',
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = client.get('/api/v1/auth/check-login-id?login_id=taken')

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'login_id': 'taken', 'available': False}


class TestUpdateMyCredentialsEndpoint:
    """Test cases for PATCH /auth/me/credentials."""

    def test_update_login_id_email_and_password(self, client: TestClient, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(str(user_id), 'annotator', test_settings)
        current_hash = hash_password('current-password')
        current_record = {
            'id': user_id,
            'name': 'User',
            'login_id': 'oldid',
            'email': 'old@example.com',
            'role': 'annotator',
            'password_hash': current_hash,
            'must_change_password': True,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        updated_record = {
            **current_record,
            'login_id': 'newid',
            'email': 'new@example.com',
            'must_change_password': False,
        }

        with (
            patch(
                'saegim.repositories.user_repo.get_with_password_by_id',
                new_callable=AsyncMock,
                return_value=current_record,
            ),
            patch(
                'saegim.repositories.user_repo.is_login_id_taken',
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                'saegim.repositories.user_repo.is_email_taken',
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                'saegim.repositories.user_repo.update_credentials',
                new_callable=AsyncMock,
                return_value=updated_record,
            ) as mock_update,
        ):
            response = client.patch(
                '/api/v1/auth/me/credentials',
                headers={'Authorization': f'Bearer {token}'},
                json={
                    'current_password': 'current-password',
                    'login_id': 'newid',
                    'email': 'new@example.com',
                    'new_password': 'new-password123',
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['must_change_password'] is False
        assert 'access_token' in data
        assert mock_update.call_args.kwargs['login_id'] == 'newid'
        assert mock_update.call_args.kwargs['email'] == 'new@example.com'
        assert mock_update.call_args.kwargs['password_hash'] != current_hash

    def test_invalid_current_password_returns_401(self, client: TestClient, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(str(user_id), 'annotator', test_settings)
        current_record = {
            'id': user_id,
            'name': 'User',
            'login_id': 'userid',
            'email': 'user@example.com',
            'role': 'annotator',
            'password_hash': hash_password('correct-password'),
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_with_password_by_id',
            new_callable=AsyncMock,
            return_value=current_record,
        ):
            response = client.patch(
                '/api/v1/auth/me/credentials',
                headers={'Authorization': f'Bearer {token}'},
                json={'current_password': 'wrong-password', 'login_id': 'newid'},
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_duplicate_login_id_returns_409(self, client: TestClient, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(str(user_id), 'annotator', test_settings)
        current_record = {
            'id': user_id,
            'name': 'User',
            'login_id': 'userid',
            'email': 'user@example.com',
            'role': 'annotator',
            'password_hash': hash_password('current-password'),
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with (
            patch(
                'saegim.repositories.user_repo.get_with_password_by_id',
                new_callable=AsyncMock,
                return_value=current_record,
            ),
            patch(
                'saegim.repositories.user_repo.is_login_id_taken',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.patch(
                '/api/v1/auth/me/credentials',
                headers={'Authorization': f'Bearer {token}'},
                json={'current_password': 'current-password', 'login_id': 'taken'},
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_duplicate_email_returns_409(self, client: TestClient, test_settings):
        user_id = uuid.uuid4()
        token = create_access_token(str(user_id), 'annotator', test_settings)
        current_record = {
            'id': user_id,
            'name': 'User',
            'login_id': 'userid',
            'email': 'user@example.com',
            'role': 'annotator',
            'password_hash': hash_password('current-password'),
            'must_change_password': False,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with (
            patch(
                'saegim.repositories.user_repo.get_with_password_by_id',
                new_callable=AsyncMock,
                return_value=current_record,
            ),
            patch(
                'saegim.repositories.user_repo.is_login_id_taken',
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                'saegim.repositories.user_repo.is_email_taken',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.patch(
                '/api/v1/auth/me/credentials',
                headers={'Authorization': f'Bearer {token}'},
                json={'current_password': 'current-password', 'email': 'taken@example.com'},
            )

        assert response.status_code == status.HTTP_409_CONFLICT
