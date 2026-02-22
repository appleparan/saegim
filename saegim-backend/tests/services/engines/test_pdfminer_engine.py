"""Tests for PdfminerEngine."""

from pathlib import Path

import pytest

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.pdfminer_engine import PdfminerEngine


class TestPdfminerEngine:
    def test_is_base_ocr_engine_subclass(self):
        engine = PdfminerEngine()
        assert isinstance(engine, BaseOCREngine)

    def test_extract_page_raises_not_implemented(self):
        engine = PdfminerEngine()
        with pytest.raises(NotImplementedError, match='does not support image-based'):
            engine.extract_page(Path('/fake/image.png'), 1200, 1600)

    def test_test_connection_returns_success(self):
        engine = PdfminerEngine()
        success, message = engine.test_connection()
        assert success is True
        assert 'pdfminer' in message
        assert 'no external service' in message
