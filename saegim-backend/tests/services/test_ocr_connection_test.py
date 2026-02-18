"""Tests for OCR connection test service (2-stage pipeline)."""

from unittest.mock import MagicMock, patch

import httpx

from saegim.services.ocr_connection_test import (
    check_gemini_connection,
    check_ocr_connection,
    check_ppstructure_connection,
    check_vllm_connection,
)


class TestPpstructureConnection:
    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_successful_connection(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        success, message = check_ppstructure_connection(
            {'host': 'localhost', 'port': 18811},
        )
        assert success is True
        assert 'localhost:18811' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_connection_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError('refused')
        mock_client_cls.return_value = mock_client

        success, message = check_ppstructure_connection(
            {'host': 'localhost', 'port': 18811},
        )
        assert success is False
        assert 'Cannot connect' in message


class TestGeminiConnection:
    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_successful_connection(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {'displayName': 'Gemini 2.0 Flash'}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        success, message = check_gemini_connection(
            {'api_key': 'test-key', 'model': 'gemini-2.0-flash'},
        )
        assert success is True
        assert 'Gemini 2.0 Flash' in message

    def test_missing_api_key(self):
        success, message = check_gemini_connection({})
        assert success is False
        assert 'API key' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_invalid_api_key(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        error = httpx.HTTPStatusError(
            'Forbidden',
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = error
        mock_client_cls.return_value = mock_client

        success, message = check_gemini_connection({'api_key': 'bad-key'})
        assert success is False
        assert 'Invalid API key' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_model_not_found(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        error = httpx.HTTPStatusError(
            'Not found',
            request=MagicMock(),
            response=mock_response,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = error
        mock_client_cls.return_value = mock_client

        success, message = check_gemini_connection(
            {'api_key': 'key', 'model': 'bad-model'},
        )
        assert success is False
        assert 'Model not found' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_connection_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError('refused')
        mock_client_cls.return_value = mock_client

        success, message = check_gemini_connection({'api_key': 'key'})
        assert success is False
        assert 'Connection failed' in message


class TestVllmConnection:
    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_successful_connection(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [{'id': 'allenai/olmOCR-2-7B-1025'}],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        success, message = check_vllm_connection(
            {'host': 'localhost', 'port': 8000},
        )
        assert success is True
        assert 'olmOCR' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_connection_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.ConnectError('refused')
        mock_client_cls.return_value = mock_client

        success, message = check_vllm_connection(
            {'host': 'localhost', 'port': 9999},
        )
        assert success is False
        assert 'Cannot connect' in message

    @patch('saegim.services.ocr_connection_test.httpx.Client')
    def test_empty_models_list(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': []}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        success, message = check_vllm_connection(
            {'host': 'gpu-server', 'port': 8000},
        )
        assert success is True
        assert 'gpu-server:8000' in message


class TestOcrConnection:
    def test_pymupdf_no_test_needed(self):
        success, message = check_ocr_connection({'layout_provider': 'pymupdf'})
        assert success is True
        assert 'does not require' in message

    def test_unknown_layout_provider(self):
        success, message = check_ocr_connection({'layout_provider': 'unknown'})
        assert success is False
        assert 'Unknown layout provider' in message

    @patch('saegim.services.ocr_connection_test.check_ppstructure_connection')
    @patch('saegim.services.ocr_connection_test.check_gemini_connection')
    def test_ppstructure_gemini(self, mock_gemini, mock_pp):
        mock_pp.return_value = (True, 'PP ok')
        mock_gemini.return_value = (True, 'Gemini ok')

        success, message = check_ocr_connection(
            {
                'layout_provider': 'ppstructure',
                'ocr_provider': 'gemini',
                'ppstructure': {'host': 'h', 'port': 18811},
                'gemini': {'api_key': 'k'},
            }
        )
        assert success is True
        assert 'PP ok' in message
        assert 'Gemini ok' in message

    @patch('saegim.services.ocr_connection_test.check_ppstructure_connection')
    @patch('saegim.services.ocr_connection_test.check_vllm_connection')
    def test_ppstructure_olmocr(self, mock_vllm, mock_pp):
        mock_pp.return_value = (True, 'PP ok')
        mock_vllm.return_value = (True, 'vLLM ok')

        success, _message = check_ocr_connection(
            {
                'layout_provider': 'ppstructure',
                'ocr_provider': 'olmocr',
                'ppstructure': {'host': 'h', 'port': 18811},
                'vllm': {'host': 'h', 'port': 8000},
            }
        )
        assert success is True
        mock_vllm.assert_called_once()

    @patch('saegim.services.ocr_connection_test.check_ppstructure_connection')
    def test_ppstructure_ppocr(self, mock_pp):
        mock_pp.return_value = (True, 'PP ok')

        success, message = check_ocr_connection(
            {
                'layout_provider': 'ppstructure',
                'ocr_provider': 'ppocr',
                'ppstructure': {'host': 'h', 'port': 18811},
            }
        )
        assert success is True
        assert 'PP-OCR built-in' in message

    @patch('saegim.services.ocr_connection_test.check_ppstructure_connection')
    def test_ppstructure_fails(self, mock_pp):
        mock_pp.return_value = (False, 'Cannot connect')

        success, message = check_ocr_connection(
            {
                'layout_provider': 'ppstructure',
                'ocr_provider': 'gemini',
                'ppstructure': {'host': 'h', 'port': 18811},
                'gemini': {'api_key': 'k'},
            }
        )
        assert success is False
        assert 'Cannot connect' in message
