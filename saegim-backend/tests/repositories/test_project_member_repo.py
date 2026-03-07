"""Tests for project_member_repo."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from saegim.repositories import project_member_repo


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_member_record(user_id):
    return {
        'user_id': user_id,
        'user_name': 'Test User',
        'user_email': 'test@example.com',
        'role': 'annotator',
        'joined_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestAdd:
    @pytest.mark.asyncio
    async def test_success(self, mock_pool, project_id, user_id, sample_member_record):
        mock_pool.execute.return_value = 'INSERT 0 1'
        mock_pool.fetchrow.return_value = sample_member_record

        result = await project_member_repo.add(mock_pool, project_id, user_id, 'annotator')

        mock_pool.execute.assert_called_once()
        mock_pool.fetchrow.assert_called_once()
        assert result == sample_member_record

    @pytest.mark.asyncio
    async def test_default_role(self, mock_pool, project_id, user_id, sample_member_record):
        mock_pool.execute.return_value = 'INSERT 0 1'
        mock_pool.fetchrow.return_value = sample_member_record

        await project_member_repo.add(mock_pool, project_id, user_id)

        call_args = mock_pool.execute.call_args
        assert call_args[0][3] == 'annotator'


class TestGetRole:
    @pytest.mark.asyncio
    async def test_found(self, mock_pool, project_id, user_id):
        mock_pool.fetchrow.return_value = {'role': 'owner'}

        result = await project_member_repo.get_role(mock_pool, project_id, user_id)

        assert result == 'owner'

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool, project_id, user_id):
        mock_pool.fetchrow.return_value = None

        result = await project_member_repo.get_role(mock_pool, project_id, user_id)

        assert result is None


class TestListByProject:
    @pytest.mark.asyncio
    async def test_returns_members(self, mock_pool, project_id, sample_member_record):
        mock_pool.fetch.return_value = [sample_member_record]

        result = await project_member_repo.list_by_project(mock_pool, project_id)

        assert len(result) == 1
        assert result[0] == sample_member_record

    @pytest.mark.asyncio
    async def test_empty_project(self, mock_pool, project_id):
        mock_pool.fetch.return_value = []

        result = await project_member_repo.list_by_project(mock_pool, project_id)

        assert result == []


class TestUpdateRole:
    @pytest.mark.asyncio
    async def test_success(self, mock_pool, project_id, user_id, sample_member_record):
        updated = {**sample_member_record, 'role': 'reviewer'}
        mock_pool.execute.return_value = 'UPDATE 1'
        mock_pool.fetchrow.return_value = updated

        result = await project_member_repo.update_role(mock_pool, project_id, user_id, 'reviewer')

        assert result is not None
        assert result['role'] == 'reviewer'

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool, project_id, user_id):
        mock_pool.execute.return_value = 'UPDATE 0'

        result = await project_member_repo.update_role(mock_pool, project_id, user_id, 'reviewer')

        assert result is None


class TestRemove:
    @pytest.mark.asyncio
    async def test_success(self, mock_pool, project_id, user_id):
        mock_pool.execute.return_value = 'DELETE 1'

        result = await project_member_repo.remove(mock_pool, project_id, user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_not_found(self, mock_pool, project_id, user_id):
        mock_pool.execute.return_value = 'DELETE 0'

        result = await project_member_repo.remove(mock_pool, project_id, user_id)

        assert result is False


class TestListProjectsForUser:
    @pytest.mark.asyncio
    async def test_returns_projects(self, mock_pool, user_id):
        project_record = {
            'id': uuid.uuid4(),
            'name': 'Project 1',
            'description': 'Test',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        mock_pool.fetch.return_value = [project_record]

        result = await project_member_repo.list_projects_for_user(mock_pool, user_id)

        assert len(result) == 1
        assert result[0]['name'] == 'Project 1'
