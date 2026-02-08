"""Tests for document endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient


class TestDocumentEndpoints:
    """Test cases for document API endpoints."""

    def test_get_document(self, client: TestClient, sample_document_record):
        doc_id = sample_document_record['id']
        with patch(
            'saegim.repositories.document_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=sample_document_record,
        ):
            response = client.get(f'/api/v1/documents/{doc_id}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['filename'] == 'test.pdf'
        assert data['status'] == 'ready'
        assert data['total_pages'] == 5

    def test_get_document_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.document_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get('/api/v1/documents/00000000-0000-0000-0000-000000000000')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_document_project_not_found(self, client: TestClient):
        with patch(
            'saegim.repositories.project_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.post(
                '/api/v1/projects/00000000-0000-0000-0000-000000000000/documents',
                files={'file': ('test.pdf', b'%PDF-1.4 fake', 'application/pdf')},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_document_not_pdf(self, client: TestClient, sample_project_record):
        project_id = sample_project_record['id']
        with patch(
            'saegim.repositories.project_repo.get_by_id',
            new_callable=AsyncMock,
            return_value=sample_project_record,
        ):
            response = client.post(
                f'/api/v1/projects/{project_id}/documents',
                files={'file': ('test.txt', b'not a pdf', 'text/plain')},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'PDF' in response.json()['detail']

    def test_list_document_pages(self, client: TestClient, sample_document_record):
        doc_id = sample_document_record['id']
        mock_pages = [
            {
                'id': '00000000-0000-0000-0000-000000000001',
                'page_no': 1,
                'width': 1200,
                'height': 1600,
                'status': 'pending',
                'assigned_to': None,
                'updated_at': '2024-01-01T00:00:00+00:00',
            },
        ]
        with (
            patch(
                'saegim.repositories.document_repo.get_by_id',
                new_callable=AsyncMock,
                return_value=sample_document_record,
            ),
            patch(
                'saegim.repositories.page_repo.list_by_document',
                new_callable=AsyncMock,
                return_value=mock_pages,
            ),
        ):
            response = client.get(f'/api/v1/documents/{doc_id}/pages')

        assert response.status_code == status.HTTP_200_OK
