"""Tests for 2-stage OCR pipeline orchestrator."""

import io
from unittest.mock import MagicMock

from PIL import Image

from saegim.services.ocr_pipeline import (
    OcrPipeline,
    _build_layout_det,
    _crop_region,
)
from saegim.services.ppstructure_service import LayoutRegion


def _make_test_image(width: int = 800, height: int = 1200):
    """Create a simple test image."""
    img = Image.new('RGB', (width, height), color='white')
    return img


def _make_test_image_path(tmp_path, width: int = 800, height: int = 1200):
    """Create a test image file and return its path."""
    img = _make_test_image(width, height)
    path = tmp_path / 'test_page.png'
    img.save(path, format='PNG')
    img.close()
    return path


class TestCropRegion:
    def test_crop_basic(self):
        img = _make_test_image(100, 100)
        result = _crop_region(img, (10.0, 20.0, 50.0, 60.0))
        # Verify it returns valid PNG bytes
        cropped = Image.open(io.BytesIO(result))
        assert cropped.size == (40, 40)
        img.close()
        cropped.close()

    def test_crop_clamped_to_bounds(self):
        img = _make_test_image(100, 100)
        result = _crop_region(img, (-10.0, -5.0, 200.0, 150.0))
        cropped = Image.open(io.BytesIO(result))
        assert cropped.size == (100, 100)
        img.close()
        cropped.close()

    def test_crop_zero_area_returns_empty(self):
        img = _make_test_image(100, 100)
        result = _crop_region(img, (50.0, 50.0, 50.0, 50.0))
        assert result == b''
        img.close()


class TestBuildLayoutDet:
    def test_text_region(self):
        region = LayoutRegion(
            bbox=(10.0, 20.0, 300.0, 60.0),
            category='text_block',
            score=0.9,
        )
        det = _build_layout_det(region, 'Hello world', order=0)

        assert det['category_type'] == 'text_block'
        assert det['poly'] == [10.0, 20.0, 300.0, 20.0, 300.0, 60.0, 10.0, 60.0]
        assert det['text'] == 'Hello world'
        assert det['order'] == 0
        assert det['anno_id'] == 0
        assert det['ignore'] is False

    def test_equation_region_uses_latex(self):
        region = LayoutRegion(
            bbox=(10.0, 20.0, 100.0, 50.0),
            category='equation_isolated',
            score=0.85,
        )
        det = _build_layout_det(region, 'E=mc^2', order=1)

        assert det['latex'] == 'E=mc^2'
        assert 'text' not in det

    def test_table_region_uses_html(self):
        region = LayoutRegion(
            bbox=(10.0, 20.0, 400.0, 300.0),
            category='table',
            score=0.92,
        )
        det = _build_layout_det(region, '| A | B |', order=2)

        assert det['html'] == '| A | B |'
        assert 'text' not in det

    def test_empty_text_no_text_key(self):
        region = LayoutRegion(
            bbox=(10.0, 20.0, 100.0, 100.0),
            category='figure',
            score=0.95,
        )
        det = _build_layout_det(region, '', order=0)

        assert 'text' not in det
        assert 'latex' not in det
        assert 'html' not in det


class TestOcrPipeline:
    def test_extract_page_with_text_provider(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)

        mock_layout_client = MagicMock()
        mock_layout_client.detect_layout.return_value = [
            LayoutRegion(bbox=(10.0, 20.0, 300.0, 60.0), category='title', score=0.95),
            LayoutRegion(bbox=(10.0, 80.0, 300.0, 400.0), category='text_block', score=0.88),
        ]

        mock_text_provider = MagicMock()
        mock_text_provider.extract_text.side_effect = ['Chapter 1', 'Body text here']

        pipeline = OcrPipeline(mock_layout_client, mock_text_provider)
        result = pipeline.extract_page(image_path, 800, 1200)

        assert len(result['layout_dets']) == 2
        assert result['layout_dets'][0]['category_type'] == 'title'
        assert result['layout_dets'][0]['text'] == 'Chapter 1'
        assert result['layout_dets'][1]['text'] == 'Body text here'
        assert mock_text_provider.extract_text.call_count == 2

    def test_extract_page_builtin_ocr(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)

        mock_layout_client = MagicMock()
        mock_layout_client.detect_layout.return_value = [
            LayoutRegion(
                bbox=(10.0, 20.0, 300.0, 60.0),
                category='title',
                score=0.95,
                text='PP-OCR Title',
            ),
        ]

        pipeline = OcrPipeline(mock_layout_client, use_builtin_ocr=True)
        result = pipeline.extract_page(image_path, 800, 1200)

        assert len(result['layout_dets']) == 1
        assert result['layout_dets'][0]['text'] == 'PP-OCR Title'

    def test_extract_page_no_regions(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)

        mock_layout_client = MagicMock()
        mock_layout_client.detect_layout.return_value = []

        pipeline = OcrPipeline(mock_layout_client)
        result = pipeline.extract_page(image_path, 800, 1200)

        assert result['layout_dets'] == []
        assert result['page_attribute'] == {}
        assert result['extra'] == {'relation': []}

    def test_extract_page_skips_figures(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)

        mock_layout_client = MagicMock()
        mock_layout_client.detect_layout.return_value = [
            LayoutRegion(bbox=(10.0, 20.0, 300.0, 300.0), category='figure', score=0.9),
            LayoutRegion(bbox=(10.0, 320.0, 300.0, 400.0), category='text_block', score=0.8),
        ]

        mock_text_provider = MagicMock()
        mock_text_provider.extract_text.return_value = 'Some text'

        pipeline = OcrPipeline(mock_layout_client, mock_text_provider)
        result = pipeline.extract_page(image_path, 800, 1200)

        assert len(result['layout_dets']) == 2
        # Figure should have no text
        assert 'text' not in result['layout_dets'][0]
        # Text provider called only once (for text_block, not figure)
        assert mock_text_provider.extract_text.call_count == 1

    def test_extract_page_no_text_provider(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)

        mock_layout_client = MagicMock()
        mock_layout_client.detect_layout.return_value = [
            LayoutRegion(bbox=(10.0, 20.0, 300.0, 60.0), category='title', score=0.95),
        ]

        pipeline = OcrPipeline(mock_layout_client)
        result = pipeline.extract_page(image_path, 800, 1200)

        # With no text provider and no builtin OCR, text should be empty
        assert 'text' not in result['layout_dets'][0]
