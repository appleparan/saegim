"""Tests for auth dependency functions."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from saegim.api.deps import (
    _hash_token,
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    hash_password,
    rotate_refresh_token,
    set_refresh_cookie,
    validate_refresh_token,
    verify_password,
)
from saegim.api.settings import Settings


@pytest.fixture
def test_settings():
    return Settings(
        secret_key='test-secret-key-32chars-for-testing',
        jwt_algorithm='HS256',
        access_token_expire_minutes=60,
        refresh_token_expire_days=7,
        refresh_cookie_name='saegim_refresh_token',
        refresh_cookie_secure=False,
        refresh_cookie_samesite='lax',
        refresh_grace_period_seconds=30,
    )


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.execute = AsyncMock()
    return pool


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password('mypassword')
        assert hashed != 'mypassword'
        assert verify_password('mypassword', hashed)

    def test_wrong_password(self):
        hashed = hash_password('correctpassword')
        assert not verify_password('wrongpassword', hashed)

    def test_different_hashes_same_password(self):
        hash1 = hash_password('samepassword')
        hash2 = hash_password('samepassword')
        assert hash1 != hash2  # bcrypt uses random salt
        assert verify_password('samepassword', hash1)
        assert verify_password('samepassword', hash2)


class TestCreateAccessToken:
    def test_creates_valid_token(self, test_settings):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id, 'annotator', test_settings)

        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        assert payload['sub'] == user_id
        assert payload['role'] == 'annotator'
        assert 'exp' in payload

    def test_admin_role_in_token(self, test_settings):
        token = create_access_token(str(uuid.uuid4()), 'admin', test_settings)
        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        assert payload['role'] == 'admin'

    def test_token_expiry(self, test_settings):
        token = create_access_token(str(uuid.uuid4()), 'annotator', test_settings)
        payload = jwt.decode(
            token,
            test_settings.secret_key,
            algorithms=[test_settings.jwt_algorithm],
        )
        exp = datetime.datetime.fromtimestamp(payload['exp'], tz=datetime.UTC)
        now = datetime.datetime.now(tz=datetime.UTC)
        delta = exp - now
        # Should expire in ~60 minutes (test_settings)
        assert 59 <= delta.total_seconds() / 60 <= 61

    def test_expired_token_raises(self, test_settings):
        expired_settings = Settings(
            secret_key=test_settings.secret_key,
            jwt_algorithm='HS256',
            access_token_expire_minutes=-1,
        )
        token = create_access_token(str(uuid.uuid4()), 'annotator', expired_settings)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token,
                test_settings.secret_key,
                algorithms=[test_settings.jwt_algorithm],
            )


class TestHashToken:
    def test_consistent_hash(self):
        assert _hash_token('abc') == _hash_token('abc')

    def test_different_inputs_different_hashes(self):
        assert _hash_token('abc') != _hash_token('def')

    def test_returns_hex_string(self):
        result = _hash_token('test')
        assert len(result) == 64
        assert all(c in '0123456789abcdef' for c in result)


class TestCreateRefreshToken:
    @pytest.mark.asyncio
    async def test_creates_token_with_new_family(self, test_settings, mock_pool):
        user_id = uuid.uuid4()
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'token_hash': 'h' * 64,
            'family_id': uuid.uuid4(),
            'expires_at': datetime.datetime.now(tz=datetime.UTC),
            'revoked_at': None,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        raw_token, record = await create_refresh_token(user_id, test_settings, mock_pool)

        assert len(raw_token) == 64  # 32 bytes hex
        assert record is not None
        call_args = mock_pool.fetchrow.call_args[0]
        assert call_args[1] == user_id

    @pytest.mark.asyncio
    async def test_creates_token_with_existing_family(self, test_settings, mock_pool):
        user_id = uuid.uuid4()
        family_id = uuid.uuid4()
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'token_hash': 'h' * 64,
            'family_id': family_id,
            'expires_at': datetime.datetime.now(tz=datetime.UTC),
            'revoked_at': None,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        raw_token, _record = await create_refresh_token(
            user_id, test_settings, mock_pool, family_id=family_id
        )

        assert len(raw_token) == 64
        call_args = mock_pool.fetchrow.call_args[0]
        assert call_args[3] == family_id


class TestValidateRefreshToken:
    @pytest.mark.asyncio
    async def test_valid_active_token(self, test_settings, mock_pool):
        user_id = uuid.uuid4()
        family_id = uuid.uuid4()
        raw_token = 'a' * 64
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'token_hash': _hash_token(raw_token),
            'family_id': family_id,
            'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
            'revoked_at': None,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        result_user_id, result_family_id = await validate_refresh_token(
            raw_token, mock_pool, test_settings
        )
        assert result_user_id == user_id
        assert result_family_id == family_id

    @pytest.mark.asyncio
    async def test_invalid_token_not_found(self, test_settings, mock_pool):
        mock_pool.fetchrow.return_value = None

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await validate_refresh_token('nonexistent', mock_pool, test_settings)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token(self, test_settings, mock_pool):
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': uuid.uuid4(),
            'token_hash': 'h' * 64,
            'family_id': uuid.uuid4(),
            'expires_at': datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=1),
            'revoked_at': None,
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await validate_refresh_token('token', mock_pool, test_settings)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_revoked_within_grace_period(self, test_settings, mock_pool):
        user_id = uuid.uuid4()
        family_id = uuid.uuid4()
        raw_token = 'b' * 64
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': user_id,
            'token_hash': _hash_token(raw_token),
            'family_id': family_id,
            'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
            'revoked_at': datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(seconds=5),
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        result_user_id, result_family_id = await validate_refresh_token(
            raw_token, mock_pool, test_settings
        )
        assert result_user_id == user_id
        assert result_family_id == family_id

    @pytest.mark.asyncio
    async def test_revoked_past_grace_period_revokes_family(self, test_settings, mock_pool):
        family_id = uuid.uuid4()
        mock_pool.fetchrow.return_value = {
            'id': uuid.uuid4(),
            'user_id': uuid.uuid4(),
            'token_hash': 'h' * 64,
            'family_id': family_id,
            'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
            'revoked_at': datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(seconds=60),
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await validate_refresh_token('token', mock_pool, test_settings)
        assert exc_info.value.status_code == 401
        mock_pool.execute.assert_called_once()


class TestRotateRefreshToken:
    @pytest.mark.asyncio
    async def test_revokes_old_and_creates_new(self, test_settings, mock_pool):
        user_id = uuid.uuid4()
        family_id = uuid.uuid4()
        old_token = 'old_token'
        old_id = uuid.uuid4()

        # First call: get_by_token_hash for old token
        # Second call: create new token
        mock_pool.fetchrow.side_effect = [
            {
                'id': old_id,
                'user_id': user_id,
                'token_hash': _hash_token(old_token),
                'family_id': family_id,
                'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
                'revoked_at': None,
                'created_at': datetime.datetime.now(tz=datetime.UTC),
            },
            {
                'id': uuid.uuid4(),
                'user_id': user_id,
                'token_hash': 'new_hash',
                'family_id': family_id,
                'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
                'revoked_at': None,
                'created_at': datetime.datetime.now(tz=datetime.UTC),
            },
        ]

        new_token, new_record = await rotate_refresh_token(
            old_token, user_id, family_id, test_settings, mock_pool
        )

        assert len(new_token) == 64
        assert new_record is not None
        mock_pool.execute.assert_called_once()


class TestRefreshCookieHelpers:
    def test_set_refresh_cookie(self, test_settings):
        response = MagicMock()
        set_refresh_cookie(response, 'my-token', test_settings)
        response.set_cookie.assert_called_once_with(
            key='saegim_refresh_token',
            value='my-token',
            httponly=True,
            secure=False,
            samesite='lax',
            max_age=7 * 86400,
            path='/api/v1/auth',
        )

    def test_clear_refresh_cookie(self, test_settings):
        response = MagicMock()
        clear_refresh_cookie(response, test_settings)
        response.delete_cookie.assert_called_once_with(
            key='saegim_refresh_token',
            httponly=True,
            secure=False,
            samesite='lax',
            path='/api/v1/auth',
        )
