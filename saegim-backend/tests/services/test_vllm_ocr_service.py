"""Tests for vLLM OCR service."""

import json
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.vllm_ocr_service import VllmOcrProvider, _parse_vllm_response


class TestParseVllmResponse:
    """Test vLLM response parsing."""

    def test_parse_valid_response(self):
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Hello', 'order': 0},
        ]
        response = {
            'choices': [{'message': {'content': json.dumps(elements)}}],
        }
        result = _parse_vllm_response(response)
        assert len(result) == 1
        assert result[0]['category_type'] == 'title'

    def test_parse_markdown_wrapped_response(self):
        elements = [
            {'category_type': 'text_block', 'bbox': [0, 0, 100, 50], 'text': 'Body', 'order': 0},
        ]
        text = f'```json\n{json.dumps(elements)}\n```'
        response = {'choices': [{'message': {'content': text}}]}
        result = _parse_vllm_response(response)
        assert len(result) == 1
        assert result[0]['category_type'] == 'text_block'

    def test_parse_empty_choices(self):
        assert _parse_vllm_response({'choices': []}) == []

    def test_parse_empty_content(self):
        assert _parse_vllm_response({'choices': [{'message': {'content': ''}}]}) == []

    def test_parse_invalid_json(self):
        response = {'choices': [{'message': {'content': 'not json at all'}}]}
        assert _parse_vllm_response(response) == []

    def test_parse_non_list_json(self):
        response = {'choices': [{'message': {'content': '{"key": "val"}'}}]}
        assert _parse_vllm_response(response) == []


class TestVllmOcrProvider:
    """Test VllmOcrProvider.extract_page()."""

    def test_base_url(self):
        provider = VllmOcrProvider(host='10.0.0.1', port=9090)
        assert provider.base_url == 'http://10.0.0.1:9090'

    def test_extract_page_success(self, tmp_path):
        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake image data')

        elements = [
            {
                'category_type': 'text_block',
                'bbox': [50, 100, 500, 300],
                'text': 'Hello world',
                'order': 0,
            },
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': json.dumps(elements)}}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch('saegim.services.vllm_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            provider = VllmOcrProvider(host='localhost', port=8000, model='test-model')
            result = provider.extract_page(image_path, page_width=800, page_height=1200)

        assert 'layout_dets' in result
        assert len(result['layout_dets']) == 1
        det = result['layout_dets'][0]
        assert det['category_type'] == 'text_block'
        assert det['poly'] == [50, 100, 500, 100, 500, 300, 50, 300]
        assert det['text'] == 'Hello world'

    def test_extract_page_api_error(self, tmp_path):
        import httpx

        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake')

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        error = httpx.HTTPStatusError('error', request=MagicMock(), response=mock_response)

        with patch('saegim.services.vllm_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock()
            mock_client.post.return_value.raise_for_status.side_effect = error
            mock_client_cls.return_value = mock_client

            provider = VllmOcrProvider()
            with pytest.raises(RuntimeError, match='vLLM API returned 500'):
                provider.extract_page(image_path, 800, 1200)

    def test_extract_page_connection_error(self, tmp_path):
        import httpx

        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake')

        with patch('saegim.services.vllm_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError('Connection refused')
            mock_client_cls.return_value = mock_client

            provider = VllmOcrProvider()
            with pytest.raises(RuntimeError, match='vLLM API request failed'):
                provider.extract_page(image_path, 800, 1200)
