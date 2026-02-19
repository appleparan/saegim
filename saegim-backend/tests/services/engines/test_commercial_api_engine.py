"""Tests for CommercialApiEngine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.commercial_api_engine import CommercialApiEngine


class TestCommercialApiEngineInit:
    def test_gemini_provider_creates_engine(self):
        config = {'api_key': 'test-key', 'model': 'gemini-3-flash-preview'}
        engine = CommercialApiEngine(provider='gemini', config=config)
        assert isinstance(engine, BaseOCREngine)

    def test_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match='Unknown commercial API provider'):
            CommercialApiEngine(provider='unknown', config={})


class TestCommercialApiEngineExtractPage:
    def test_gemini_delegates_extract_page(self):
        config = {'api_key': 'test-key', 'model': 'gemini-3-flash-preview'}
        engine = CommercialApiEngine(provider='gemini', config=config)

        expected = {'layout_dets': [], 'page_attribute': {}, 'extra': {'relation': []}}
        engine._provider = MagicMock()
        engine._provider.extract_page.return_value = expected

        result = engine.extract_page(Path('/fake/image.png'), 1200, 1600)
        assert result == expected
        engine._provider.extract_page.assert_called_once_with(
            Path('/fake/image.png'), 1200, 1600
        )


class TestCommercialApiEngineTestConnection:
    @patch('saegim.services.engines.commercial_api_engine.check_gemini_connection')
    def test_gemini_connection_test(self, mock_check):
        mock_check.return_value = (True, 'Connected to Gemini')
        config = {'api_key': 'test-key', 'model': 'gemini-3-flash-preview'}
        engine = CommercialApiEngine(provider='gemini', config=config)

        success, message = engine.test_connection()
        assert success is True
        assert 'Gemini' in message
        mock_check.assert_called_once_with(config)

    @patch('saegim.services.engines.commercial_api_engine.check_gemini_connection')
    def test_connection_test_failure(self, mock_check):
        mock_check.return_value = (False, 'Invalid API key')
        config = {'api_key': 'bad-key'}
        engine = CommercialApiEngine(provider='gemini', config=config)

        success, message = engine.test_connection()
        assert success is False
        assert 'Invalid API key' in message

    def test_unknown_provider_connection_test(self):
        config = {'api_key': 'test-key', 'model': 'gemini-3-flash-preview'}
        engine = CommercialApiEngine(provider='gemini', config=config)
        engine._provider_name = 'unknown'

        success, message = engine.test_connection()
        assert success is False
        assert 'Unknown provider' in message
