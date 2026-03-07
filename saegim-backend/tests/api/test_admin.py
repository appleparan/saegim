"""Tests for admin-only endpoints."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import create_access_token
from saegim.api.settings import Settings


def _make_admin_token(test_settings: Settings) -> str:
    return create_access_token(str(uuid.uuid4()), 'admin', test_settings)


def _make_annotator_token(test_settings: Settings) -> str:
    return create_access_token(str(uuid.uuid4()), 'annotator', test_settings)


def _admin_record(user_id: uuid.UUID | None = None) -> dict:
    return {
        'id': user_id or uuid.uuid4(),
        'name': 'Admin',
        'email': 'admin@example.com',
        'role': 'admin',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


class TestAdminListUsers:
    def test_no_auth_returns_401(self, client: TestClient):
        response = client.get('/api/v1/admin/users')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_returns_403(self, client: TestClient, test_settings: Settings):
        token = _make_annotator_token(test_settings)
        annotator_record = {
            'id': uuid.uuid4(),
            'name': 'User',
            'email': 'user@example.com',
            'role': 'annotator',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=annotator_record,
        ):
            response = client.get(
                '/api/v1/admin/users',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_success(self, client: TestClient, test_settings: Settings):
        admin_rec = _admin_record()
        token = create_access_token(str(admin_rec['id']), 'admin', test_settings)
        user_records = [admin_rec]
        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin_rec,
            ),
            patch(
                'saegim.repositories.user_repo.list_all',
                new_callable=AsyncMock,
                return_value=user_records,
            ),
        ):
            response = client.get(
                '/api/v1/admin/users',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


class TestAdminUpdateUser:
    def test_update_role(self, client: TestClient, test_settings: Settings):
        admin_rec = _admin_record()
        target_id = uuid.uuid4()
        updated_record = {
            'id': target_id,
            'name': 'Target',
            'email': 'target@example.com',
            'role': 'reviewer',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        token = create_access_token(str(admin_rec['id']), 'admin', test_settings)
        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin_rec,
            ),
            patch(
                'saegim.repositories.user_repo.update_role',
                new_callable=AsyncMock,
                return_value=updated_record,
            ),
        ):
            response = client.patch(
                f'/api/v1/admin/users/{target_id}',
                headers={'Authorization': f'Bearer {token}'},
                json={'role': 'reviewer'},
            )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['role'] == 'reviewer'

    def test_user_not_found(self, client: TestClient, test_settings: Settings):
        admin_rec = _admin_record()
        token = create_access_token(str(admin_rec['id']), 'admin', test_settings)
        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin_rec,
            ),
            patch(
                'saegim.repositories.user_repo.update_role',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.patch(
                f'/api/v1/admin/users/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
                json={'role': 'reviewer'},
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_no_fields_returns_400(self, client: TestClient, test_settings: Settings):
        admin_rec = _admin_record()
        token = create_access_token(str(admin_rec['id']), 'admin', test_settings)
        with patch(
            'saegim.repositories.user_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=admin_rec,
        ):
            response = client.patch(
                f'/api/v1/admin/users/{uuid.uuid4()}',
                headers={'Authorization': f'Bearer {token}'},
                json={},
            )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAdminListProjects:
    def test_admin_success(self, client: TestClient, test_settings: Settings):
        admin_rec = _admin_record()
        token = create_access_token(str(admin_rec['id']), 'admin', test_settings)
        project_records = [
            {
                'id': uuid.uuid4(),
                'name': 'Project 1',
                'description': 'Test',
                'created_at': datetime.datetime.now(tz=datetime.UTC),
            },
        ]
        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin_rec,
            ),
            patch(
                'saegim.repositories.project_repo.list_all',
                new_callable=AsyncMock,
                return_value=project_records,
            ),
        ):
            response = client.get(
                '/api/v1/admin/projects',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == 'Project 1'

    def test_non_admin_returns_403(self, client: TestClient, test_settings: Settings):
        token = _make_annotator_token(test_settings)
        annotator_record = {
            'id': uuid.uuid4(),
            'name': 'User',
            'email': 'user@example.com',
            'role': 'annotator',
            'created_at': datetime.datetime.now(tz=datetime.UTC),
        }
        with patch(
            'saegim.repositories.user_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=annotator_record,
        ):
            response = client.get(
                '/api/v1/admin/projects',
                headers={'Authorization': f'Bearer {token}'},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN
