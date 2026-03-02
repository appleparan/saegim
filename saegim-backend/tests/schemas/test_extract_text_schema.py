"""Tests for ExtractTextRequest schema with engine_type field."""

import pytest

from saegim.schemas.page import ExtractTextRequest


class TestExtractTextRequest:
    def test_default_engine_type_is_none(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
        )
        assert req.engine_type is None
        assert req.category_type == 'text_block'

    def test_engine_type_override(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
            engine_type='commercial_api',
        )
        assert req.engine_type == 'commercial_api'

    def test_engine_type_vllm(self):
        req = ExtractTextRequest(
            poly=[0, 0, 100, 0, 100, 100, 0, 100],
            engine_type='vllm',
        )
        assert req.engine_type == 'vllm'

    def test_poly_validation_min_length(self):
        with pytest.raises(ValueError, match=r'ensure this value has at least 8|too_short'):
            ExtractTextRequest(poly=[0, 0, 100, 0])

    def test_poly_validation_max_length(self):
        with pytest.raises(ValueError, match=r'ensure this value has at most 8|too_long'):
            ExtractTextRequest(poly=[0] * 10)
