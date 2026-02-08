"""Pytest configuration and fixtures for API tests."""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from saegim.api.settings import Settings, get_settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with overrides for testing.

    Returns:
        Settings: Test configuration settings.
    """
    return Settings(
        debug=True,
        log_level='DEBUG',
        api_host='127.0.0.1',
        api_port=5000,
        cors_origins=['http://localhost:3000'],
        max_workers=1,
        model_name='test_model',
        model_path='tests/fixtures/models/',
        max_batch_size=10,
        timeout_seconds=5.0,
        database_url='postgresql://test:test@localhost:5432/test',
        storage_path='./test_storage',
    )


@pytest.fixture
def mock_pool():
    """Create a mock asyncpg pool.

    Returns:
        MagicMock: Mock pool with async methods.
    """
    pool = MagicMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    pool.acquire = MagicMock()
    return pool


@pytest.fixture
def app(test_settings: Settings, mock_pool):
    """Create FastAPI app instance for testing with mocked DB.

    Args:
        test_settings: Test configuration settings.
        mock_pool: Mock database pool.

    Yields:
        FastAPI: Test FastAPI application instance.
    """

    def get_test_settings():
        return test_settings

    with (
        patch('saegim.app.create_pool', new_callable=AsyncMock),
        patch('saegim.app.close_pool', new_callable=AsyncMock),
        patch('saegim.core.database._pool', mock_pool),
        patch('saegim.core.database.get_pool', return_value=mock_pool),
    ):
        from saegim.app import create_app

        app = create_app(settings=test_settings)
        app.dependency_overrides[get_settings] = get_test_settings

        yield app

        app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Create test client for API testing.

    Args:
        app: FastAPI application instance.

    Returns:
        TestClient: FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def sample_prediction_data():
    """Sample data for prediction tests.

    Returns:
        list: Sample input data for predictions.
    """
    return [
        {'feature1': 1.0, 'feature2': 2.0},
        {'feature1': 3.0, 'feature2': 4.0},
        {'feature1': 5.0, 'feature2': 6.0},
    ]


@pytest.fixture
def sample_project_record():
    """Sample project database record.

    Returns:
        dict: Mock project record.
    """
    return {
        'id': uuid.uuid4(),
        'name': 'Test Project',
        'description': 'A test project',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


@pytest.fixture
def sample_document_record(sample_project_record):
    """Sample document database record.

    Args:
        sample_project_record: Sample project record fixture.

    Returns:
        dict: Mock document record.
    """
    return {
        'id': uuid.uuid4(),
        'project_id': sample_project_record['id'],
        'filename': 'test.pdf',
        'pdf_path': '/storage/pdfs/test.pdf',
        'total_pages': 5,
        'status': 'ready',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }


@pytest.fixture
def sample_page_record(sample_document_record):
    """Sample page database record with annotation data.

    Args:
        sample_document_record: Sample document record fixture.

    Returns:
        dict: Mock page record.
    """
    return {
        'id': uuid.uuid4(),
        'document_id': sample_document_record['id'],
        'page_no': 1,
        'width': 1200,
        'height': 1600,
        'image_path': '/storage/images/test_p1.png',
        'annotation_data': {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 200, 300, 200, 300, 400, 100, 400],
                    'ignore': False,
                    'order': 0,
                    'anno_id': 0,
                    'text': 'Sample text',
                    'attribute': {
                        'text_language': 'text_ko',
                        'text_background': 'white',
                        'text_rotate': 'normal',
                    },
                    'line_with_spans': [],
                    'merge_list': [],
                    'latex': '',
                    'html': '',
                },
            ],
            'page_attribute': {
                'data_source': 'academic_literature',
                'language': 'ko',
                'layout': 'single_column',
                'watermark': False,
                'fuzzy_scan': False,
                'colorful_background': False,
            },
            'extra': {'relation': []},
        },
        'auto_extracted_data': None,
        'status': 'pending',
        'assigned_to': None,
        'locked_at': None,
        'updated_at': datetime.datetime.now(tz=datetime.UTC),
    }


@pytest.fixture
def sample_user_record():
    """Sample user database record.

    Returns:
        dict: Mock user record.
    """
    return {
        'id': uuid.uuid4(),
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'annotator',
        'created_at': datetime.datetime.now(tz=datetime.UTC),
    }
