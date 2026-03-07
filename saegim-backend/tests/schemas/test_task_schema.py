"""Tests for task workflow schemas."""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from saegim.schemas.task import (
    AssignRequest,
    ReviewAction,
    ReviewQueueItem,
    ReviewRequest,
    TaskHistoryEntry,
    TaskResponse,
)


class TestReviewAction:
    def test_approved_value(self):
        assert ReviewAction.APPROVED == 'approved'

    def test_rejected_value(self):
        assert ReviewAction.REJECTED == 'rejected'


class TestAssignRequest:
    def test_valid_assign(self):
        uid = uuid.uuid4()
        req = AssignRequest(user_id=uid)
        assert req.user_id == uid

    def test_invalid_uuid(self):
        with pytest.raises(ValidationError):
            AssignRequest(user_id='not-a-uuid')


class TestReviewRequest:
    def test_approved_without_comment(self):
        req = ReviewRequest(action=ReviewAction.APPROVED)
        assert req.action == ReviewAction.APPROVED
        assert req.comment is None

    def test_rejected_with_comment(self):
        req = ReviewRequest(action=ReviewAction.REJECTED, comment='Needs more detail')
        assert req.action == ReviewAction.REJECTED
        assert req.comment == 'Needs more detail'

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            ReviewRequest(action='invalid')

    def test_comment_too_long(self):
        with pytest.raises(ValidationError):
            ReviewRequest(action=ReviewAction.APPROVED, comment='x' * 2001)


class TestTaskResponse:
    def test_valid_task_response(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        resp = TaskResponse(
            page_id=uuid.uuid4(),
            page_no=1,
            document_id=uuid.uuid4(),
            document_filename='test.pdf',
            project_id=uuid.uuid4(),
            project_name='Test Project',
            status='in_progress',
            assigned_at=now,
        )
        assert resp.page_no == 1
        assert resp.status == 'in_progress'


class TestReviewQueueItem:
    def test_valid_review_queue_item(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        item = ReviewQueueItem(
            page_id=uuid.uuid4(),
            page_no=3,
            document_id=uuid.uuid4(),
            document_filename='doc.pdf',
            assigned_to=uuid.uuid4(),
            assigned_to_name='Test User',
            submitted_at=now,
        )
        assert item.page_no == 3
        assert item.assigned_to_name == 'Test User'

    def test_optional_assigned_fields(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        item = ReviewQueueItem(
            page_id=uuid.uuid4(),
            page_no=1,
            document_id=uuid.uuid4(),
            document_filename='doc.pdf',
            submitted_at=now,
        )
        assert item.assigned_to is None
        assert item.assigned_to_name is None


class TestTaskHistoryEntry:
    def test_valid_entry(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        entry = TaskHistoryEntry(
            id=uuid.uuid4(),
            page_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action='assigned',
            created_at=now,
        )
        assert entry.action == 'assigned'
        assert entry.snapshot is None

    def test_entry_with_snapshot(self):
        now = datetime.datetime.now(tz=datetime.UTC)
        entry = TaskHistoryEntry(
            id=uuid.uuid4(),
            page_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action='submitted',
            snapshot={'status': 'submitted'},
            created_at=now,
        )
        assert entry.snapshot == {'status': 'submitted'}
