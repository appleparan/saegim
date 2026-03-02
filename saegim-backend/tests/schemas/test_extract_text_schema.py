"""Tests for ExtractTextRequest schema with engine_id field."""

import pytest

from saegim.schemas.page import ExtractTextRequest


class TestExtractTextRequest:
    def test_default_engine_id_is_none(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
        )
        assert req.engine_id is None
        assert req.category_type == 'text_block'

    def test_engine_id_override(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
            engine_id='gemini-flash',
        )
        assert req.engine_id == 'gemini-flash'

    def test_engine_id_vllm_instance(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
            engine_id='vllm-chandra',
        )
        assert req.engine_id == 'vllm-chandra'

    def test_poly_validation_min_length(self):
        with pytest.raises(ValueError, match=r'ensure this value has at least 8|too_short'):
            ExtractTextRequest(poly=[0, 0, 100, 0])

    def test_poly_validation_max_length(self):
        with pytest.raises(ValueError, match=r'ensure this value has at most 8|too_long'):
            ExtractTextRequest(poly=[0] * 10)
