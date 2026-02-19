"""Tests for Gemini OCR service."""

import json
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.gemini_ocr_service import (
    GeminiOcrProvider,
    GeminiTextOcrProvider,
    _extract_text_from_gemini,
    _parse_gemini_response,
)


class TestParseGeminiResponse:
    """Test Gemini response parsing."""

    def test_parse_valid_response(self):
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Hello', 'order': 0},
            {'category_type': 'text_block', 'bbox': [10, 80, 400, 200], 'text': 'Body', 'order': 1},
        ]
        response = {
            'candidates': [
                {
                    'content': {
                        'parts': [{'text': json.dumps(elements)}],
                    },
                },
            ],
        }
        result = _parse_gemini_response(response)
        assert len(result) == 2
        assert result[0]['category_type'] == 'title'
        assert result[1]['text'] == 'Body'

    def test_parse_markdown_wrapped_response(self):
        elements = [
            {'category_type': 'title', 'bbox': [0, 0, 100, 50], 'text': 'Title', 'order': 0},
        ]
        text = f'```json\n{json.dumps(elements)}\n```'
        response = {
            'candidates': [{'content': {'parts': [{'text': text}]}}],
        }
        result = _parse_gemini_response(response)
        assert len(result) == 1
        assert result[0]['category_type'] == 'title'

    def test_parse_empty_candidates(self):
        result = _parse_gemini_response({'candidates': []})
        assert result == []

    def test_parse_no_parts(self):
        result = _parse_gemini_response({'candidates': [{'content': {'parts': []}}]})
        assert result == []

    def test_parse_invalid_json(self):
        response = {
            'candidates': [{'content': {'parts': [{'text': 'not json'}]}}],
        }
        result = _parse_gemini_response(response)
        assert result == []

    def test_parse_non_list_json(self):
        response = {
            'candidates': [{'content': {'parts': [{'text': '{"key": "value"}'}]}}],
        }
        result = _parse_gemini_response(response)
        assert result == []


class TestGeminiOcrProvider:
    """Test GeminiOcrProvider.extract_page()."""

    def test_extract_page_success(self, tmp_path):
        # Create a dummy image file
        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake image data')

        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Title', 'order': 0},
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': json.dumps(elements)}]}}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch('saegim.services.gemini_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            provider = GeminiOcrProvider(api_key='test-key', model='gemini-3-flash-preview')
            result = provider.extract_page(image_path, page_width=800, page_height=1200)

        assert 'layout_dets' in result
        assert len(result['layout_dets']) == 1
        assert result['layout_dets'][0]['category_type'] == 'title'
        assert result['layout_dets'][0]['poly'] == [10, 20, 400, 20, 400, 60, 10, 60]
        assert result['layout_dets'][0]['text'] == 'Title'

    def test_extract_page_api_error(self, tmp_path):
        import httpx

        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake')

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        error = httpx.HTTPStatusError('error', request=MagicMock(), response=mock_response)

        with patch('saegim.services.gemini_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock()
            mock_client.post.return_value.raise_for_status.side_effect = error
            mock_client_cls.return_value = mock_client

            provider = GeminiOcrProvider(api_key='bad-key')
            with pytest.raises(RuntimeError, match='Gemini API returned 403'):
                provider.extract_page(image_path, 800, 1200)

    def test_extract_page_empty_response(self, tmp_path):
        image_path = tmp_path / 'test.png'
        image_path.write_bytes(b'\x89PNG\r\n\x1a\nfake')

        mock_response = MagicMock()
        mock_response.json.return_value = {'candidates': []}
        mock_response.raise_for_status = MagicMock()

        with patch('saegim.services.gemini_ocr_service.httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            provider = GeminiOcrProvider(api_key='test-key')
            result = provider.extract_page(image_path, 800, 1200)

        assert result['layout_dets'] == []


class TestExtractTextFromGemini:
    def test_extract_text_success(self):
        result = {
            'candidates': [
                {'content': {'parts': [{'text': 'Hello World'}]}},
            ],
        }
        assert _extract_text_from_gemini(result) == 'Hello World'

    def test_extract_text_empty_candidates(self):
        assert _extract_text_from_gemini({'candidates': []}) == ''

    def test_extract_text_empty_parts(self):
        result = {'candidates': [{'content': {'parts': []}}]}
        assert _extract_text_from_gemini(result) == ''

    def test_extract_text_strips_whitespace(self):
        result = {
            'candidates': [
                {'content': {'parts': [{'text': '  trimmed  '}]}},
            ],
        }
        assert _extract_text_from_gemini(result) == 'trimmed'


class TestGeminiTextOcrProvider:
    @patch('saegim.services.gemini_ocr_service.httpx.Client')
    def test_extract_text_success(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'candidates': [
                {'content': {'parts': [{'text': 'Extracted text'}]}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        provider = GeminiTextOcrProvider(api_key='test-key')
        result = provider.extract_text(b'fake-png-bytes', 'text_block')

        assert result == 'Extracted text'
        mock_client.post.assert_called_once()

    @patch('saegim.services.gemini_ocr_service.httpx.Client')
    def test_extract_text_table_category(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'candidates': [
                {'content': {'parts': [{'text': '| A | B |\n|---|---|\n| 1 | 2 |'}]}},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        provider = GeminiTextOcrProvider(api_key='test-key')
        result = provider.extract_text(b'fake-png-bytes', 'table')

        assert '| A | B |' in result

    @patch('saegim.services.gemini_ocr_service.httpx.Client')
    def test_extract_text_api_error(self, mock_client_cls):
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        error = httpx.HTTPStatusError(
            'error',
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = MagicMock()
        mock_client.post.return_value.raise_for_status.side_effect = error
        mock_client_cls.return_value = mock_client

        provider = GeminiTextOcrProvider(api_key='bad-key')
        with pytest.raises(RuntimeError, match='Gemini API returned 403'):
            provider.extract_text(b'fake-png-bytes')

    @patch('saegim.services.gemini_ocr_service.httpx.Client')
    def test_extract_text_empty_response(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {'candidates': []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        provider = GeminiTextOcrProvider(api_key='test-key')
        result = provider.extract_text(b'fake-png-bytes')

        assert result == ''
