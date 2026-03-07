"""Tests for refresh token repository functions."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from saegim.repositories import refresh_token_repo


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_token_record():
    return {
        'id': uuid.uuid4(),
        'user_id': uuid.uuid4(),
        'token_hash': 'a' * 64,
        'family_id': uuid.uuid4(),
        'expires_at': datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=7),
        'revoked_at': None,
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestRefreshTokenRepoCreate:
    @pytest.mark.asyncio
    async def test_create(self, mock_pool, sample_token_record):
        mock_pool.fetchrow.return_value = sample_token_record
        result = await refresh_token_repo.create(
            mock_pool,
            sample_token_record['user_id'],
            sample_token_record['token_hash'],
            sample_token_record['family_id'],
            sample_token_record['expires_at'],
        )
        assert result == sample_token_record
        call_args = mock_pool.fetchrow.call_args[0]
        assert 'INSERT INTO refresh_tokens' in call_args[0]
        assert call_args[1] == sample_token_record['user_id']
        assert call_args[2] == sample_token_record['token_hash']
        assert call_args[3] == sample_token_record['family_id']
        assert call_args[4] == sample_token_record['expires_at']


class TestRefreshTokenRepoGetByTokenHash:
    @pytest.mark.asyncio
    async def test_found(self, mock_pool, sample_token_record):
        mock_pool.fetchrow.return_value = sample_token_record
        result = await refresh_token_repo.get_by_token_hash(mock_pool, 'a' * 64)
        assert result == sample_token_record
        call_sql = mock_pool.fetchrow.call_args[0][0]
        assert 'token_hash' in call_sql

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        result = await refresh_token_repo.get_by_token_hash(mock_pool, 'nonexistent')
        assert result is None


class TestRefreshTokenRepoRevoke:
    @pytest.mark.asyncio
    async def test_revoke(self, mock_pool):
        token_id = uuid.uuid4()
        await refresh_token_repo.revoke(mock_pool, token_id)
        mock_pool.execute.assert_called_once()
        call_args = mock_pool.execute.call_args[0]
        assert 'revoked_at' in call_args[0]
        assert call_args[1] == token_id


class TestRefreshTokenRepoRevokeFamily:
    @pytest.mark.asyncio
    async def test_revoke_family(self, mock_pool):
        family_id = uuid.uuid4()
        await refresh_token_repo.revoke_family(mock_pool, family_id)
        mock_pool.execute.assert_called_once()
        call_args = mock_pool.execute.call_args[0]
        assert 'family_id' in call_args[0]
        assert 'revoked_at IS NULL' in call_args[0]
        assert call_args[1] == family_id


class TestRefreshTokenRepoDeleteAllForUser:
    @pytest.mark.asyncio
    async def test_delete_all_for_user(self, mock_pool):
        user_id = uuid.uuid4()
        await refresh_token_repo.delete_all_for_user(mock_pool, user_id)
        mock_pool.execute.assert_called_once()
        call_args = mock_pool.execute.call_args[0]
        assert 'DELETE FROM refresh_tokens' in call_args[0]
        assert 'user_id' in call_args[0]
        assert call_args[1] == user_id


class TestRefreshTokenRepoDeleteExpired:
    @pytest.mark.asyncio
    async def test_delete_expired(self, mock_pool):
        mock_pool.execute.return_value = 'DELETE 3'
        count = await refresh_token_repo.delete_expired(mock_pool)
        assert count == 3
        call_sql = mock_pool.execute.call_args[0][0]
        assert 'expires_at < NOW()' in call_sql

    @pytest.mark.asyncio
    async def test_delete_expired_none(self, mock_pool):
        mock_pool.execute.return_value = 'DELETE 0'
        count = await refresh_token_repo.delete_expired(mock_pool)
        assert count == 0
