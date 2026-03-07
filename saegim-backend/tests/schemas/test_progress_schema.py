"""Tests for project progress board schemas."""

import uuid

from saegim.schemas.progress import (
    DocumentProgress,
    MemberActivity,
    ProjectProgressResponse,
    StatusBreakdown,
)


class TestStatusBreakdown:
    def test_valid_creation(self):
        sb = StatusBreakdown(pending=10, in_progress=5, submitted=3, reviewed=2)
        assert sb.pending == 10
        assert sb.in_progress == 5
        assert sb.submitted == 3
        assert sb.reviewed == 2

    def test_zero_counts(self):
        sb = StatusBreakdown(pending=0, in_progress=0, submitted=0, reviewed=0)
        assert sb.pending == 0


class TestDocumentProgress:
    def test_valid_creation(self):
        doc_id = uuid.uuid4()
        dp = DocumentProgress(
            document_id=doc_id,
            filename='test.pdf',
            total_pages=20,
            status_counts=StatusBreakdown(pending=10, in_progress=5, submitted=3, reviewed=2),
            completion_rate=10.0,
        )
        assert dp.document_id == doc_id
        assert dp.filename == 'test.pdf'
        assert dp.total_pages == 20
        assert dp.completion_rate == 10.0
        assert dp.status_counts.reviewed == 2

    def test_zero_completion(self):
        dp = DocumentProgress(
            document_id=uuid.uuid4(),
            filename='empty.pdf',
            total_pages=0,
            status_counts=StatusBreakdown(pending=0, in_progress=0, submitted=0, reviewed=0),
            completion_rate=0.0,
        )
        assert dp.completion_rate == 0.0


class TestMemberActivity:
    def test_valid_creation(self):
        uid = uuid.uuid4()
        ma = MemberActivity(
            user_id=uid,
            user_name='Test User',
            role='annotator',
            assigned_pages=10,
            in_progress_pages=5,
            submitted_pages=3,
            reviewed_pages=2,
        )
        assert ma.user_id == uid
        assert ma.user_name == 'Test User'
        assert ma.role == 'annotator'
        assert ma.assigned_pages == 10

    def test_no_activity(self):
        ma = MemberActivity(
            user_id=uuid.uuid4(),
            user_name='Idle User',
            role='reviewer',
            assigned_pages=0,
            in_progress_pages=0,
            submitted_pages=0,
            reviewed_pages=0,
        )
        assert ma.assigned_pages == 0


class TestProjectProgressResponse:
    def test_full_response(self):
        resp = ProjectProgressResponse(
            total_pages=100,
            completion_rate=25.0,
            status_breakdown=StatusBreakdown(pending=40, in_progress=20, submitted=15, reviewed=25),
            documents=[
                DocumentProgress(
                    document_id=uuid.uuid4(),
                    filename='doc1.pdf',
                    total_pages=50,
                    status_counts=StatusBreakdown(
                        pending=20, in_progress=10, submitted=10, reviewed=10
                    ),
                    completion_rate=20.0,
                ),
            ],
            members=[
                MemberActivity(
                    user_id=uuid.uuid4(),
                    user_name='Worker',
                    role='annotator',
                    assigned_pages=30,
                    in_progress_pages=15,
                    submitted_pages=10,
                    reviewed_pages=5,
                ),
            ],
        )
        assert resp.total_pages == 100
        assert resp.completion_rate == 25.0
        assert len(resp.documents) == 1
        assert len(resp.members) == 1

    def test_empty_project(self):
        resp = ProjectProgressResponse(
            total_pages=0,
            completion_rate=0.0,
            status_breakdown=StatusBreakdown(pending=0, in_progress=0, submitted=0, reviewed=0),
            documents=[],
            members=[],
        )
        assert resp.total_pages == 0
        assert resp.documents == []
        assert resp.members == []
