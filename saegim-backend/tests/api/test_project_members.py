"""Tests for project member management endpoints."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import create_access_token, get_current_user, require_project_member
from saegim.api.settings import Settings


@pytest.fixture(autouse=True)
def _clear_auth_override(app):
    """Remove global auth overrides for member tests."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_project_member, None)
    return


def _make_token(
    test_settings: Settings, user_id: uuid.UUID | None = None, role: str = 'annotator'
) -> str:
    return create_access_token(str(user_id or uuid.uuid4()), role, test_settings)


def _user_record(
    user_id: uuid.UUID | None = None,
    role: str = 'annotator',
    name: str = 'User',
    email: str = 'user@example.com',
) -> dict:
    return {
        'id': user_id or uuid.uuid4(),
        'name': name,
        'email': email,
        'role': role,
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


def _project_record(project_id: uuid.UUID | None = None) -> dict:
    return {
        'id': project_id or uuid.uuid4(),
        'name': 'Test Project',
        'description': 'A test project',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


def _member_record(user_id: uuid.UUID | None = None, role: str = 'annotator') -> dict:
    uid = user_id or uuid.uuid4()
    return {
        'user_id': uid,
        'user_name': 'Member',
        'user_email': 'member@example.com',
        'role': role,
        'joined_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestListMembers:
    def test_success_as_member(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)
        owner_rec = _user_record(owner_id)
        member_rec = _member_record(owner_id, 'owner')

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=owner_rec,
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.list_by_project',
                new_callable=AsyncMock,
                return_value=[member_rec],
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['role'] == 'owner'

    def test_non_member_returns_403(self, client: TestClient, test_settings: Settings):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, user_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(user_id),
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_view_any_project(self, client: TestClient, test_settings: Settings):
        admin_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, admin_id, 'admin')
        admin_rec = _user_record(admin_id, 'admin')

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin_rec,
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.list_by_project',
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_200_OK

    def test_project_not_found(self, client: TestClient, test_settings: Settings):
        user_id = uuid.uuid4()
        token = _make_token(test_settings, user_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(user_id),
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{uuid.uuid4()}/members',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAddMember:
    def test_owner_can_add(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        target_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)
        member_rec = _member_record(target_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                side_effect=[
                    _user_record(owner_id),  # get_current_user
                    _user_record(target_id, email='target@example.com'),  # target user check
                ],
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.add',
                new_callable=AsyncMock,
                return_value=member_rec,
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
                json={'user_id': str(target_id), 'role': 'annotator'},
            )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['role'] == 'annotator'

    def test_non_owner_returns_403(self, client: TestClient, test_settings: Settings):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, user_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(user_id),
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
                json={'user_id': str(uuid.uuid4()), 'role': 'annotator'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_add(self, client: TestClient, test_settings: Settings):
        admin_id = uuid.uuid4()
        target_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, admin_id, 'admin')
        member_rec = _member_record(target_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                side_effect=[
                    _user_record(admin_id, 'admin'),
                    _user_record(target_id),
                ],
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.add',
                new_callable=AsyncMock,
                return_value=member_rec,
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
                json={'user_id': str(target_id), 'role': 'annotator'},
            )
        assert response.status_code == status.HTTP_201_CREATED

    def test_duplicate_returns_409(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        target_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                side_effect=[
                    _user_record(owner_id),
                    _user_record(target_id),
                ],
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.add',
                new_callable=AsyncMock,
                side_effect=asyncpg.UniqueViolationError(),
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
                json={'user_id': str(target_id), 'role': 'annotator'},
            )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_user_not_found_returns_404(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                side_effect=[
                    _user_record(owner_id),
                    None,  # target user not found
                ],
            ),
            patch(
                'saegim.repositories.project_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_project_record(project_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/members',
                headers={'Authorization': f'Bearer {token}'},
                json={'user_id': str(uuid.uuid4()), 'role': 'annotator'},
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateMemberRole:
    def test_owner_can_update(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        target_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)
        updated_rec = _member_record(target_id, 'reviewer')

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(owner_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.update_role',
                new_callable=AsyncMock,
                return_value=updated_rec,
            ),
        ):
            response = client.patch(
                f'/api/v1/projects/{project_id}/members/{target_id}',
                headers={'Authorization': f'Bearer {token}'},
                json={'role': 'reviewer'},
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['role'] == 'reviewer'

    def test_non_owner_returns_403(self, client: TestClient, test_settings: Settings):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, user_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(user_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
        ):
            response = client.patch(
                f'/api/v1/projects/{project_id}/members/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
                json={'role': 'reviewer'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_not_found(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(owner_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.update_role',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.patch(
                f'/api/v1/projects/{project_id}/members/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
                json={'role': 'reviewer'},
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRemoveMember:
    def test_owner_can_remove(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        target_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(owner_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.remove',
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/members/{target_id}',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_non_owner_returns_403(self, client: TestClient, test_settings: Settings):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, user_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(user_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/members/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_member_not_found(self, client: TestClient, test_settings: Settings):
        owner_id = uuid.uuid4()
        project_id = uuid.uuid4()
        token = _make_token(test_settings, owner_id)

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=_user_record(owner_id),
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.project_member_repo.remove',
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            response = client.delete(
                f'/api/v1/projects/{project_id}/members/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND
