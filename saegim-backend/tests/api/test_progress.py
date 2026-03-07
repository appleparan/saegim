"""Tests for project progress board endpoint."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import create_access_token, get_current_user, require_project_member
from saegim.api.settings import Settings


@pytest.fixture(autouse=True)
def _clear_auth_override(app):
    """Remove global auth overrides for progress tests."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_project_member, None)
    return


def _user_record(role='annotator', user_id=None):
    email = f'{role}@example.com'
    return {
        'id': user_id or uuid.uuid4(),
        'name': f'Test {role.capitalize()}',
        'login_id': email,
        'email': email,
        'role': role,
        'must_change_password': False,
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


def _auth_headers(user_record, settings):
    token = create_access_token(str(user_record['id']), user_record['role'], settings)
    return {'Authorization': f'Bearer {token}'}


def _summary_record():
    return {
        'total_pages': 20,
        'pending': 5,
        'in_progress': 6,
        'submitted': 4,
        'reviewed': 5,
    }


def _doc_records():
    return [
        {
            'document_id': uuid.uuid4(),
            'filename': 'doc1.pdf',
            'total_pages': 12,
            'pending': 3,
            'in_progress': 4,
            'submitted': 2,
            'reviewed': 3,
        },
        {
            'document_id': uuid.uuid4(),
            'filename': 'doc2.pdf',
            'total_pages': 8,
            'pending': 2,
            'in_progress': 2,
            'submitted': 2,
            'reviewed': 2,
        },
    ]


def _member_records():
    return [
        {
            'user_id': uuid.uuid4(),
            'user_name': 'Alice',
            'role': 'annotator',
            'assigned_pages': 10,
            'in_progress_pages': 5,
            'submitted_pages': 3,
            'reviewed_pages': 2,
        },
        {
            'user_id': uuid.uuid4(),
            'user_name': 'Bob',
            'role': 'reviewer',
            'assigned_pages': 0,
            'in_progress_pages': 0,
            'submitted_pages': 0,
            'reviewed_pages': 0,
        },
    ]


class TestGetProjectProgress:
    def test_returns_full_progress(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        project_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=user,
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
            patch(
                'saegim.repositories.progress_repo.get_project_status_summary',
                new_callable=AsyncMock,
                return_value=_summary_record(),
            ),
            patch(
                'saegim.repositories.progress_repo.get_document_progress',
                new_callable=AsyncMock,
                return_value=_doc_records(),
            ),
            patch(
                'saegim.repositories.progress_repo.get_member_activity',
                new_callable=AsyncMock,
                return_value=_member_records(),
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/progress',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_pages'] == 20
        assert data['completion_rate'] == 25.0
        assert data['status_breakdown']['pending'] == 5
        assert data['status_breakdown']['reviewed'] == 5
        assert len(data['documents']) == 2
        assert data['documents'][0]['filename'] == 'doc1.pdf'
        assert len(data['members']) == 2
        assert data['members'][0]['user_name'] == 'Alice'

    def test_empty_project(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        project_id = uuid.uuid4()
        empty_summary = {
            'total_pages': 0,
            'pending': 0,
            'in_progress': 0,
            'submitted': 0,
            'reviewed': 0,
        }

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=user,
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
            patch(
                'saegim.repositories.progress_repo.get_project_status_summary',
                new_callable=AsyncMock,
                return_value=empty_summary,
            ),
            patch(
                'saegim.repositories.progress_repo.get_document_progress',
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                'saegim.repositories.progress_repo.get_member_activity',
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/progress',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_pages'] == 0
        assert data['completion_rate'] == 0.0
        assert data['documents'] == []
        assert data['members'] == []

    def test_no_auth_returns_401(self, client: TestClient):
        project_id = uuid.uuid4()
        response = client.get(f'/api/v1/projects/{project_id}/progress')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_member_returns_403(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        project_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=user,
            ),
            patch(
                'saegim.repositories.project_member_repo.get_role',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/progress',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
