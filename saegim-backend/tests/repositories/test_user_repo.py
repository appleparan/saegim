"""Tests for user repository functions."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from saegim.repositories import user_repo


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_user_record():
    return {
        'id': uuid.uuid4(),
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'annotator',
        'password_hash': '$2b$12$fakehashvalue',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestUserRepoGetByEmail:
    @pytest.mark.asyncio
    async def test_found(self, mock_pool, sample_user_record):
        mock_pool.fetchrow.return_value = sample_user_record
        result = await user_repo.get_by_email(mock_pool, 'test@example.com')
        assert result == sample_user_record
        mock_pool.fetchrow.assert_called_once()
        call_sql = mock_pool.fetchrow.call_args[0][0]
        assert 'password_hash' in call_sql

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        result = await user_repo.get_by_email(mock_pool, 'nobody@example.com')
        assert result is None


class TestUserRepoCreateWithPassword:
    @pytest.mark.asyncio
    async def test_create(self, mock_pool, sample_user_record):
        mock_pool.fetchrow.return_value = sample_user_record
        result = await user_repo.create_with_password(
            mock_pool, 'Test User', 'test@example.com', '$2b$12$fakehash', 'annotator'
        )
        assert result == sample_user_record
        call_args = mock_pool.fetchrow.call_args[0]
        assert call_args[1] == 'Test User'
        assert call_args[2] == 'test@example.com'
        assert call_args[3] == '$2b$12$fakehash'
        assert call_args[4] == 'annotator'

    @pytest.mark.asyncio
    async def test_create_admin(self, mock_pool, sample_user_record):
        admin_record = {**sample_user_record, 'role': 'admin'}
        mock_pool.fetchrow.return_value = admin_record
        result = await user_repo.create_with_password(
            mock_pool, 'Admin', 'admin@example.com', '$2b$12$hash', 'admin'
        )
        assert result['role'] == 'admin'


class TestUserRepoCountAll:
    @pytest.mark.asyncio
    async def test_count(self, mock_pool):
        mock_pool.fetchrow.return_value = {'cnt': 5}
        count = await user_repo.count_all(mock_pool)
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_zero(self, mock_pool):
        mock_pool.fetchrow.return_value = {'cnt': 0}
        count = await user_repo.count_all(mock_pool)
        assert count == 0


class TestUserRepoUpdateRole:
    @pytest.mark.asyncio
    async def test_update(self, mock_pool, sample_user_record):
        updated = {**sample_user_record, 'role': 'reviewer'}
        mock_pool.fetchrow.return_value = updated
        result = await user_repo.update_role(mock_pool, sample_user_record['id'], 'reviewer')
        assert result['role'] == 'reviewer'

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        result = await user_repo.update_role(mock_pool, uuid.uuid4(), 'admin')
        assert result is None
