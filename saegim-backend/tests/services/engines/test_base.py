"""Tests for BaseOCREngine ABC."""

from pathlib import Path
from typing import Any

import pytest

from saegim.services.engines.base import BaseOCREngine


class TestBaseOCREngine:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError, match='abstract method'):
            BaseOCREngine()

    def test_subclass_must_implement_extract_page(self):
        class IncompleteEngine(BaseOCREngine):
            def test_connection(self) -> tuple[bool, str]:
                return (True, 'ok')

        with pytest.raises(TypeError, match='abstract method'):
            IncompleteEngine()

    def test_subclass_must_implement_test_connection(self):
        class IncompleteEngine(BaseOCREngine):
            def extract_page(
                self, image_path: Path, page_width: int, page_height: int
            ) -> dict[str, Any]:
                return {}

        with pytest.raises(TypeError, match='abstract method'):
            IncompleteEngine()

    def test_complete_subclass_can_be_instantiated(self):
        class ConcreteEngine(BaseOCREngine):
            def extract_page(
                self, image_path: Path, page_width: int, page_height: int
            ) -> dict[str, Any]:
                return {'layout_dets': [], 'page_attribute': {}, 'extra': {'relation': []}}

            def test_connection(self) -> tuple[bool, str]:
                return (True, 'ok')

        engine = ConcreteEngine()
        assert isinstance(engine, BaseOCREngine)
