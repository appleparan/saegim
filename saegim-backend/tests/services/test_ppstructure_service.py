"""Tests for PP-StructureV3 HTTP client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from saegim.services.ppstructure_service import (
    LayoutRegion,
    PpstructureClient,
    _map_category,
    _parse_response,
)


class TestMapCategory:
    def test_known_categories(self):
        assert _map_category('title') == 'title'
        assert _map_category('text') == 'text_block'
        assert _map_category('figure') == 'figure'
        assert _map_category('table') == 'table'
        assert _map_category('equation') == 'equation_isolated'
        assert _map_category('formula') == 'equation_isolated'
        assert _map_category('header') == 'header'
        assert _map_category('footer') == 'footer'
        assert _map_category('code') == 'code_txt'

    def test_case_insensitive(self):
        assert _map_category('Title') == 'title'
        assert _map_category('TABLE') == 'table'

    def test_unknown_defaults_to_text_block(self):
        assert _map_category('unknown_type') == 'text_block'


class TestParseResponse:
    def test_parse_flat_results(self):
        data = {
            'results': [
                {
                    'bbox': [10, 20, 300, 60],
                    'type': 'title',
                    'score': 0.95,
                    'text': 'Chapter 1',
                },
                {
                    'bbox': [10, 80, 300, 400],
                    'type': 'text',
                    'score': 0.88,
                },
            ],
        }
        regions = _parse_response(data)

        assert len(regions) == 2
        assert regions[0].bbox == (10.0, 20.0, 300.0, 60.0)
        assert regions[0].category == 'title'
        assert regions[0].score == 0.95
        assert regions[0].text == 'Chapter 1'
        assert regions[1].text is None

    def test_parse_nested_results(self):
        data = {
            'result': {
                'regions': [
                    {
                        'box': [50, 100, 600, 200],
                        'label': 'table',
                        'confidence': 0.92,
                    },
                ],
            },
        }
        regions = _parse_response(data)

        assert len(regions) == 1
        assert regions[0].bbox == (50.0, 100.0, 600.0, 200.0)
        assert regions[0].category == 'table'
        assert regions[0].score == 0.92

    def test_parse_polygon_bbox(self):
        data = {
            'results': [
                {
                    'bbox': [[10, 20], [300, 20], [300, 60], [10, 60]],
                    'type': 'title',
                    'score': 0.9,
                },
            ],
        }
        regions = _parse_response(data)

        assert regions[0].bbox == (10.0, 20.0, 300.0, 60.0)

    def test_parse_empty_results(self):
        assert _parse_response({'results': []}) == []
        assert _parse_response({}) == []

    def test_parse_with_rec_text(self):
        data = {
            'results': [
                {
                    'bbox': [10, 20, 100, 50],
                    'type': 'text',
                    'score': 0.8,
                    'rec_text': 'Hello world',
                },
            ],
        }
        regions = _parse_response(data)
        assert regions[0].text == 'Hello world'


class TestLayoutRegion:
    def test_frozen(self):
        region = LayoutRegion(
            bbox=(10.0, 20.0, 300.0, 60.0),
            category='title',
            score=0.95,
        )
        with pytest.raises(AttributeError):
            region.score = 0.5  # type: ignore[misc]

    def test_default_text_is_none(self):
        region = LayoutRegion(
            bbox=(0.0, 0.0, 100.0, 100.0),
            category='figure',
            score=0.8,
        )
        assert region.text is None


class TestPpstructureClient:
    @patch('saegim.services.ppstructure_service.httpx.Client')
    def test_detect_layout(self, mock_client_cls, tmp_path):
        # Create a fake image file
        image_file = tmp_path / 'page.png'
        image_file.write_bytes(b'fake-png-data')

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'bbox': [10, 20, 400, 60],
                    'type': 'title',
                    'score': 0.95,
                    'text': 'Title',
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        client = PpstructureClient(host='localhost', port=18811)
        regions = client.detect_layout(image_file)

        assert len(regions) == 1
        assert regions[0].category == 'title'
        assert regions[0].text == 'Title'
        mock_client.post.assert_called_once()

    @patch('saegim.services.ppstructure_service.httpx.Client')
    def test_detect_layout_connection_error(self, mock_client_cls, tmp_path):
        image_file = tmp_path / 'page.png'
        image_file.write_bytes(b'fake-png-data')

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = httpx.ConnectError('refused')
        mock_client_cls.return_value = mock_client

        client = PpstructureClient(host='localhost', port=18811)
        with pytest.raises(httpx.ConnectError):
            client.detect_layout(image_file)

    @patch('saegim.services.ppstructure_service.httpx.Client')
    def test_detect_layout_server_error(self, mock_client_cls, tmp_path):
        image_file = tmp_path / 'page.png'
        image_file.write_bytes(b'fake-png-data')

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        error = httpx.HTTPStatusError(
            'Server Error',
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = error
        mock_client_cls.return_value = mock_client

        client = PpstructureClient(host='localhost', port=18811)
        with pytest.raises(httpx.HTTPStatusError):
            client.detect_layout(image_file)
