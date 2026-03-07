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
        'login_id': 'testuser',
        'email': 'test@example.com',
        'role': 'annotator',
        'password_hash': '$2b$12$fakehashvalue',
        'must_change_password': False,
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestUserRepoGetByLoginId:
    @pytest.mark.asyncio
    async def test_found(self, mock_pool, sample_user_record):
        mock_pool.fetchrow.return_value = sample_user_record
        result = await user_repo.get_by_login_id(mock_pool, 'testuser')
        assert result == sample_user_record
        mock_pool.fetchrow.assert_called_once()
        call_sql = mock_pool.fetchrow.call_args[0][0]
        assert 'password_hash' in call_sql

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        result = await user_repo.get_by_login_id(mock_pool, 'nobody')
        assert result is None


class TestUserRepoCreateWithPassword:
    @pytest.mark.asyncio
    async def test_create(self, mock_pool, sample_user_record):
        mock_pool.fetchrow.return_value = sample_user_record
        result = await user_repo.create_with_password(
            mock_pool,
            'Test User',
            'testuser',
            '$2b$12$fakehash',
            'annotator',
            email='test@example.com',
        )
        assert result == sample_user_record
        call_args = mock_pool.fetchrow.call_args[0]
        assert call_args[1] == 'Test User'
        assert call_args[2] == 'testuser'
        assert call_args[3] == 'test@example.com'
        assert call_args[4] == '$2b$12$fakehash'
        assert call_args[5] is False
        assert call_args[6] == 'annotator'

    @pytest.mark.asyncio
    async def test_create_admin(self, mock_pool, sample_user_record):
        admin_record = {**sample_user_record, 'role': 'admin'}
        mock_pool.fetchrow.return_value = admin_record
        result = await user_repo.create_with_password(
            mock_pool,
            'Admin',
            'admin',
            '$2b$12$hash',
            'admin',
            email='admin@example.com',
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
        assert result is not None
        assert result['role'] == 'reviewer'

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        result = await user_repo.update_role(mock_pool, uuid.uuid4(), 'admin')
        assert result is None


class TestUserRepoAvailabilityChecks:
    @pytest.mark.asyncio
    async def test_login_id_taken(self, mock_pool):
        mock_pool.fetchrow.return_value = {'?column?': 1}
        taken = await user_repo.is_login_id_taken(mock_pool, 'taken-id')
        assert taken is True

    @pytest.mark.asyncio
    async def test_login_id_available(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        taken = await user_repo.is_login_id_taken(mock_pool, 'new-id')
        assert taken is False

    @pytest.mark.asyncio
    async def test_email_taken(self, mock_pool):
        mock_pool.fetchrow.return_value = {'?column?': 1}
        taken = await user_repo.is_email_taken(mock_pool, 'taken@example.com')
        assert taken is True

    @pytest.mark.asyncio
    async def test_email_available(self, mock_pool):
        mock_pool.fetchrow.return_value = None
        taken = await user_repo.is_email_taken(mock_pool, 'new@example.com')
        assert taken is False


class TestUserRepoUpdateCredentials:
    @pytest.mark.asyncio
    async def test_update_credentials_success(self, mock_pool, sample_user_record):
        updated = {**sample_user_record, 'login_id': 'newid', 'email': 'new@example.com'}
        mock_pool.fetchrow.return_value = updated

        result = await user_repo.update_credentials(
            mock_pool,
            sample_user_record['id'],
            login_id='newid',
            email='new@example.com',
            password_hash='$2b$12$newhash',
            must_change_password=False,
        )

        assert result is not None
        assert result['login_id'] == 'newid'
        assert result['email'] == 'new@example.com'

    @pytest.mark.asyncio
    async def test_update_credentials_not_found(self, mock_pool):
        mock_pool.fetchrow.return_value = None

        result = await user_repo.update_credentials(
            mock_pool,
            uuid.uuid4(),
            login_id='newid',
            email='new@example.com',
            password_hash='$2b$12$newhash',
            must_change_password=False,
        )

        assert result is None
