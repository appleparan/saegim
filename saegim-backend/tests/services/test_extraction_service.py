"""Tests for PDF text/image extraction service."""

from unittest.mock import MagicMock

import pytest

from saegim.services.extraction_service import (
    _collect_block_text,
    _overlaps_existing,
    bbox_to_poly,
    extract_page_elements,
)


class TestBboxToPoly:
    def test_converts_bbox_to_four_corner_poly(self):
        result = bbox_to_poly((10.0, 20.0, 30.0, 40.0), scale=1.0)
        assert result == [10.0, 20.0, 30.0, 20.0, 30.0, 40.0, 10.0, 40.0]

    def test_scales_coordinates_by_factor(self):
        result = bbox_to_poly((10.0, 20.0, 30.0, 40.0), scale=2.0)
        assert result == [20.0, 40.0, 60.0, 40.0, 60.0, 80.0, 20.0, 80.0]

    def test_handles_zero_bbox(self):
        result = bbox_to_poly((0.0, 0.0, 0.0, 0.0), scale=2.0)
        assert result == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def test_handles_fractional_coordinates(self):
        result = bbox_to_poly((10.5, 20.5, 30.5, 40.5), scale=2.0)
        assert result == [21.0, 41.0, 61.0, 41.0, 61.0, 81.0, 21.0, 81.0]


class TestCollectBlockText:
    def test_collects_text_from_spans(self):
        block = {
            'lines': [
                {'spans': [{'text': 'Hello '}, {'text': 'World'}]},
                {'spans': [{'text': 'Second line'}]},
            ],
        }
        assert _collect_block_text(block) == 'Hello World\nSecond line'

    def test_skips_empty_lines(self):
        block = {
            'lines': [
                {'spans': [{'text': 'Content'}]},
                {'spans': [{'text': '   '}]},
                {'spans': [{'text': 'More'}]},
            ],
        }
        assert _collect_block_text(block) == 'Content\nMore'

    def test_returns_empty_for_no_lines(self):
        assert _collect_block_text({}) == ''
        assert _collect_block_text({'lines': []}) == ''

    def test_handles_missing_text_key(self):
        block = {'lines': [{'spans': [{}]}]}
        assert _collect_block_text(block) == ''


class TestOverlapsExisting:
    def test_detects_full_overlap(self):
        poly = [0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]
        existing = [[0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]]
        assert _overlaps_existing(poly, existing) is True

    def test_no_overlap(self):
        poly = [0.0, 0.0, 50.0, 0.0, 50.0, 50.0, 0.0, 50.0]
        existing = [[200.0, 200.0, 300.0, 200.0, 300.0, 300.0, 200.0, 300.0]]
        assert _overlaps_existing(poly, existing) is False

    def test_zero_area_returns_true(self):
        poly = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        assert _overlaps_existing(poly, []) is True

    def test_empty_existing_no_overlap(self):
        poly = [0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]
        assert _overlaps_existing(poly, []) is False

    def test_partial_overlap_below_threshold(self):
        poly = [0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]
        # Overlaps only 20% of poly area
        existing = [[80.0, 80.0, 120.0, 80.0, 120.0, 120.0, 80.0, 120.0]]
        assert _overlaps_existing(poly, existing, threshold=0.5) is False


class TestExtractPageElements:
    @pytest.fixture
    def mock_page(self):
        page = MagicMock()
        page.get_images.return_value = []
        return page

    def test_extracts_text_blocks(self, mock_page):
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': (72.0, 100.0, 540.0, 200.0),
                    'lines': [
                        {'spans': [{'text': '한국어 문서 텍스트'}]},
                    ],
                },
            ],
        }

        result = extract_page_elements(mock_page, scale=2.0)

        assert len(result['layout_dets']) == 1
        el = result['layout_dets'][0]
        assert el['category_type'] == 'text_block'
        assert el['text'] == '한국어 문서 텍스트'
        assert el['anno_id'] == 0
        assert el['poly'] == [144.0, 200.0, 1080.0, 200.0, 1080.0, 400.0, 144.0, 400.0]

    def test_extracts_image_blocks(self, mock_page):
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 1,
                    'bbox': (50.0, 50.0, 300.0, 400.0),
                },
            ],
        }

        result = extract_page_elements(mock_page, scale=2.0)

        assert len(result['layout_dets']) == 1
        el = result['layout_dets'][0]
        assert el['category_type'] == 'figure'
        assert el['anno_id'] == 0
        assert 'text' not in el

    def test_skips_empty_text_blocks(self, mock_page):
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': (0.0, 0.0, 100.0, 100.0),
                    'lines': [{'spans': [{'text': '   '}]}],
                },
            ],
        }

        result = extract_page_elements(mock_page, scale=2.0)
        assert len(result['layout_dets']) == 0

    def test_empty_page_returns_empty_layout(self, mock_page):
        mock_page.get_text.return_value = {'blocks': []}

        result = extract_page_elements(mock_page, scale=2.0)

        assert result['layout_dets'] == []
        assert result['page_attribute'] == {}
        assert result['extra'] == {'relation': []}

    def test_assigns_sequential_anno_ids(self, mock_page):
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': (0.0, 0.0, 100.0, 50.0),
                    'lines': [{'spans': [{'text': 'First'}]}],
                },
                {
                    'type': 1,
                    'bbox': (0.0, 60.0, 100.0, 200.0),
                },
                {
                    'type': 0,
                    'bbox': (0.0, 210.0, 100.0, 300.0),
                    'lines': [{'spans': [{'text': 'Third'}]}],
                },
            ],
        }

        result = extract_page_elements(mock_page, scale=1.0)

        ids = [el['anno_id'] for el in result['layout_dets']]
        assert ids == [0, 1, 2]

    def test_mixed_text_and_image_blocks(self, mock_page):
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': (0.0, 0.0, 100.0, 50.0),
                    'lines': [{'spans': [{'text': 'Title text'}]}],
                },
                {
                    'type': 1,
                    'bbox': (0.0, 60.0, 200.0, 300.0),
                },
            ],
        }

        result = extract_page_elements(mock_page, scale=1.0)

        assert len(result['layout_dets']) == 2
        assert result['layout_dets'][0]['category_type'] == 'text_block'
        assert result['layout_dets'][1]['category_type'] == 'figure'

    def test_embedded_images_extracted(self):
        mock_page = MagicMock()
        mock_page.get_text.return_value = {'blocks': []}

        mock_rect = MagicMock()
        mock_rect.is_empty = False
        mock_rect.is_infinite = False
        mock_rect.x0 = 50.0
        mock_rect.y0 = 50.0
        mock_rect.x1 = 200.0
        mock_rect.y1 = 300.0

        mock_page.get_images.return_value = [(42, 0, 0, 0, 0, 0, 0)]
        mock_page.get_image_rects.return_value = [mock_rect]

        result = extract_page_elements(mock_page, scale=2.0)

        assert len(result['layout_dets']) == 1
        el = result['layout_dets'][0]
        assert el['category_type'] == 'figure'
        assert el['poly'] == [100.0, 100.0, 400.0, 100.0, 400.0, 600.0, 100.0, 600.0]

    def test_duplicate_embedded_images_skipped(self):
        mock_page = MagicMock()
        # get_text already found this image
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 1,
                    'bbox': (50.0, 50.0, 200.0, 300.0),
                },
            ],
        }

        mock_rect = MagicMock()
        mock_rect.is_empty = False
        mock_rect.is_infinite = False
        mock_rect.x0 = 50.0
        mock_rect.y0 = 50.0
        mock_rect.x1 = 200.0
        mock_rect.y1 = 300.0

        mock_page.get_images.return_value = [(42, 0, 0, 0, 0, 0, 0)]
        mock_page.get_image_rects.return_value = [mock_rect]

        result = extract_page_elements(mock_page, scale=2.0)

        # Should only have 1 figure, not 2
        figures = [el for el in result['layout_dets'] if el['category_type'] == 'figure']
        assert len(figures) == 1
