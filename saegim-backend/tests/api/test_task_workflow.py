"""Tests for task workflow endpoints (assign, submit, review)."""

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
    """Remove global get_current_user override for task workflow tests.

    Task workflow tests manage their own JWT tokens and need real auth behavior.
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


def _page_record(page_id=None, assigned_to=None, page_status='pending'):
    return {
        'id': page_id or uuid.uuid4(),
        'document_id': uuid.uuid4(),
        'page_no': 1,
        'width': 1200,
        'height': 1600,
        'image_path': '/storage/images/test_p1.png',
        'annotation_data': {'layout_dets': [], 'page_attribute': {}, 'extra': {'relation': []}},
        'auto_extracted_data': None,
        'status': page_status,
        'assigned_to': assigned_to,
        'locked_at': None,
        'updated_at': datetime.datetime.now(tz=datetime.UTC),
    }


def _auth_headers(user_record, settings):
    token = create_access_token(str(user_record['id']), user_record['role'], settings)
    return {'Authorization': f'Bearer {token}'}


class TestAssignPage:
    def test_admin_can_assign(self, client: TestClient, test_settings: Settings):
        admin = _user_record('admin')
        target_user_id = uuid.uuid4()
        page_id = uuid.uuid4()
        assigned_page = _page_record(
            page_id=page_id, assigned_to=target_user_id, page_status='in_progress'
        )

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin,
            ),
            patch(
                'saegim.repositories.task_repo.assign_page',
                new_callable=AsyncMock,
                return_value=assigned_page,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/assign',
                headers=_auth_headers(admin, test_settings),
                json={'user_id': str(target_user_id)},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'in_progress'

    def test_owner_can_assign(self, client: TestClient, test_settings: Settings):
        owner = _user_record('annotator')
        target_user_id = uuid.uuid4()
        page_id = uuid.uuid4()
        assigned_page = _page_record(
            page_id=page_id, assigned_to=target_user_id, page_status='in_progress'
        )

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=owner,
            ),
            patch(
                'saegim.repositories.task_repo.get_project_id_for_page',
                new_callable=AsyncMock,
                return_value=uuid.uuid4(),
            ),
            patch(
                'saegim.repositories.task_repo.get_project_member_role',
                new_callable=AsyncMock,
                return_value='owner',
            ),
            patch(
                'saegim.repositories.task_repo.assign_page',
                new_callable=AsyncMock,
                return_value=assigned_page,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/assign',
                headers=_auth_headers(owner, test_settings),
                json={'user_id': str(target_user_id)},
            )

        assert response.status_code == status.HTTP_200_OK

    def test_annotator_cannot_assign(self, client: TestClient, test_settings: Settings):
        annotator = _user_record('annotator')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=annotator,
            ),
            patch(
                'saegim.repositories.task_repo.get_project_id_for_page',
                new_callable=AsyncMock,
                return_value=uuid.uuid4(),
            ),
            patch(
                'saegim.repositories.task_repo.get_project_member_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/assign',
                headers=_auth_headers(annotator, test_settings),
                json={'user_id': str(uuid.uuid4())},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_no_auth_returns_401(self, client: TestClient):
        response = client.post(
            f'/api/v1/pages/{uuid.uuid4()}/assign',
            json={'user_id': str(uuid.uuid4())},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_state_returns_409(self, client: TestClient, test_settings: Settings):
        admin = _user_record('admin')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin,
            ),
            patch(
                'saegim.repositories.task_repo.assign_page',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/assign',
                headers=_auth_headers(admin, test_settings),
                json={'user_id': str(uuid.uuid4())},
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_page_not_found_returns_404(self, client: TestClient, test_settings: Settings):
        annotator = _user_record('annotator')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=annotator,
            ),
            patch(
                'saegim.repositories.task_repo.get_project_id_for_page',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/assign',
                headers=_auth_headers(annotator, test_settings),
                json={'user_id': str(uuid.uuid4())},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSubmitPage:
    def test_assigned_user_can_submit(self, client: TestClient, test_settings: Settings):
        user = _user_record('annotator')
        page_id = uuid.uuid4()
        submitted_page = _page_record(
            page_id=page_id, assigned_to=user['id'], page_status='submitted'
        )

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=user,
            ),
            patch(
                'saegim.repositories.task_repo.submit_page',
                new_callable=AsyncMock,
                return_value=submitted_page,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/submit',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'submitted'

    def test_non_assigned_user_gets_409(self, client: TestClient, test_settings: Settings):
        user = _user_record('annotator')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=user,
            ),
            patch(
                'saegim.repositories.task_repo.submit_page',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/submit',
                headers=_auth_headers(user, test_settings),
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_no_auth_returns_401(self, client: TestClient):
        response = client.post(f'/api/v1/pages/{uuid.uuid4()}/submit')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReviewPage:
    def test_admin_can_approve(self, client: TestClient, test_settings: Settings):
        admin = _user_record('admin')
        page_id = uuid.uuid4()
        reviewed_page = _page_record(page_id=page_id, page_status='reviewed')

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin,
            ),
            patch(
                'saegim.repositories.task_repo.review_page',
                new_callable=AsyncMock,
                return_value=reviewed_page,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/review',
                headers=_auth_headers(admin, test_settings),
                json={'action': 'approved'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'reviewed'

    def test_reviewer_can_reject(self, client: TestClient, test_settings: Settings):
        reviewer = _user_record('reviewer')
        page_id = uuid.uuid4()
        rejected_page = _page_record(page_id=page_id, page_status='in_progress')

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=reviewer,
            ),
            patch(
                'saegim.repositories.task_repo.get_project_id_for_page',
                new_callable=AsyncMock,
                return_value=uuid.uuid4(),
            ),
            patch(
                'saegim.repositories.task_repo.get_project_member_role',
                new_callable=AsyncMock,
                return_value='reviewer',
            ),
            patch(
                'saegim.repositories.task_repo.review_page',
                new_callable=AsyncMock,
                return_value=rejected_page,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/review',
                headers=_auth_headers(reviewer, test_settings),
                json={'action': 'rejected', 'comment': 'Needs rework'},
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'in_progress'

    def test_annotator_cannot_review(self, client: TestClient, test_settings: Settings):
        annotator = _user_record('annotator')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=annotator,
            ),
            patch(
                'saegim.repositories.task_repo.get_project_id_for_page',
                new_callable=AsyncMock,
                return_value=uuid.uuid4(),
            ),
            patch(
                'saegim.repositories.task_repo.get_project_member_role',
                new_callable=AsyncMock,
                return_value='annotator',
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/review',
                headers=_auth_headers(annotator, test_settings),
                json={'action': 'approved'},
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_action_returns_422(self, client: TestClient, test_settings: Settings):
        admin = _user_record('admin')
        with patch(
            'saegim.repositories.user_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=admin,
        ):
            response = client.post(
                f'/api/v1/pages/{uuid.uuid4()}/review',
                headers=_auth_headers(admin, test_settings),
                json={'action': 'invalid'},
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_not_submitted_returns_409(self, client: TestClient, test_settings: Settings):
        admin = _user_record('admin')
        page_id = uuid.uuid4()

        with (
            patch(
                'saegim.repositories.user_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=admin,
            ),
            patch(
                'saegim.repositories.task_repo.review_page',
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            response = client.post(
                f'/api/v1/pages/{page_id}/review',
                headers=_auth_headers(admin, test_settings),
                json={'action': 'approved'},
            )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_no_auth_returns_401(self, client: TestClient):
        response = client.post(
            f'/api/v1/pages/{uuid.uuid4()}/review',
            json={'action': 'approved'},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
