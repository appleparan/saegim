"""Tests for adapter resolver."""

from saegim.services.adapters.chandra import ChandraAdapter
from saegim.services.adapters.lightonocr import LightOnOcrAdapter
from saegim.services.adapters.paddleocr_vl import PaddleOcrVlAdapter
from saegim.services.adapters.resolver import resolve_adapter


class TestResolveAdapter:
    def test_chandra_model(self):
        adapter = resolve_adapter('datalab-to/chandra')
        assert isinstance(adapter, ChandraAdapter)

    def test_olmocr_model(self):
        adapter = resolve_adapter('allenai/olmOCR-2-7B-1025')
        assert isinstance(adapter, ChandraAdapter)

    def test_unknown_model_defaults_to_chandra(self):
        adapter = resolve_adapter('some-unknown/model')
        assert isinstance(adapter, ChandraAdapter)

    def test_lightonocr_full_name(self):
        adapter = resolve_adapter('lightonai/LightOnOCR-2-1B-bbox-soup')
        assert isinstance(adapter, LightOnOcrAdapter)

    def test_lighton_prefix(self):
        adapter = resolve_adapter('lightonai/anything')
        assert isinstance(adapter, LightOnOcrAdapter)

    def test_lightonocr_case_insensitive(self):
        adapter = resolve_adapter('LIGHTONAI/LIGHTONOCR-2-1B')
        assert isinstance(adapter, LightOnOcrAdapter)

    def test_paddleocr_vl_full_name(self):
        adapter = resolve_adapter('PaddlePaddle/PaddleOCR-VL')
        assert isinstance(adapter, PaddleOcrVlAdapter)

    def test_paddleocr_vl_case_insensitive(self):
        adapter = resolve_adapter('paddlepaddle/paddleocr-vl')
        assert isinstance(adapter, PaddleOcrVlAdapter)

    def test_paddleocr_vl_underscore(self):
        adapter = resolve_adapter('custom/paddleocr_vl_model')
        assert isinstance(adapter, PaddleOcrVlAdapter)
