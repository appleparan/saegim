"""Tests for task listing endpoints (my tasks, review queue)."""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from saegim.api.deps import create_access_token, get_current_user
from saegim.api.settings import Settings


@pytest.fixture(autouse=True)
def _clear_auth_override(app):
    """Remove global get_current_user override for task listing tests.

    Task listing tests manage their own JWT tokens and need real auth behavior.
    """
    app.dependency_overrides.pop(get_current_user, None)
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


class TestGetMyTasks:
    def test_returns_assigned_tasks(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        now = datetime.datetime.now(tz=datetime.UTC)
        task_records = [
            {
                'page_id': uuid.uuid4(),
                'page_no': 1,
                'document_id': uuid.uuid4(),
                'document_filename': 'doc1.pdf',
                'project_id': uuid.uuid4(),
                'project_name': 'Project 1',
                'status': 'in_progress',
                'assigned_at': now,
            },
            {
                'page_id': uuid.uuid4(),
                'page_no': 3,
                'document_id': uuid.uuid4(),
                'document_filename': 'doc2.pdf',
                'project_id': uuid.uuid4(),
                'project_name': 'Project 2',
                'status': 'submitted',
                'assigned_at': now,
            },
        ]

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id', new_callable=AsyncMock, return_value=user
            ),
            patch(
                'saegim.repositories.task_repo.get_user_tasks',
                new_callable=AsyncMock,
                return_value=task_records,
            ),
        ):
            response = client.get(
                '/api/v1/users/me/tasks',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]['page_no'] == 1
        assert data[1]['status'] == 'submitted'

    def test_returns_empty_list(self, client: TestClient, test_settings: Settings):
        user = _user_record()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id', new_callable=AsyncMock, return_value=user
            ),
            patch(
                'saegim.repositories.task_repo.get_user_tasks',
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = client.get(
                '/api/v1/users/me/tasks',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_no_auth_returns_401(self, client: TestClient):
        response = client.get('/api/v1/users/me/tasks')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetReviewQueue:
    def test_returns_submitted_pages(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        project_id = uuid.uuid4()
        now = datetime.datetime.now(tz=datetime.UTC)
        queue_records = [
            {
                'page_id': uuid.uuid4(),
                'page_no': 2,
                'document_id': uuid.uuid4(),
                'document_filename': 'doc1.pdf',
                'assigned_to': uuid.uuid4(),
                'assigned_to_name': 'Worker',
                'submitted_at': now,
            },
        ]

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id', new_callable=AsyncMock, return_value=user
            ),
            patch(
                'saegim.repositories.task_repo.get_review_queue',
                new_callable=AsyncMock,
                return_value=queue_records,
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/review-queue',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['assigned_to_name'] == 'Worker'

    def test_returns_empty_queue(self, client: TestClient, test_settings: Settings):
        user = _user_record()
        project_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id', new_callable=AsyncMock, return_value=user
            ),
            patch(
                'saegim.repositories.task_repo.get_review_queue',
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            response = client.get(
                f'/api/v1/projects/{project_id}/review-queue',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_no_auth_returns_401(self, client: TestClient):
        response = client.get(f'/api/v1/projects/{uuid.uuid4()}/review-queue')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
