"""Tests for PDF text/image extraction service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from saegim.services.extraction_service import (
    _flip_bbox,
    _is_zero_area,
    _overlaps_existing,
    bbox_to_poly,
    extract_page_elements,
)

_MODULE = 'saegim.services.extraction_service'


# --- Fake pdfminer layout classes for isinstance checks ---


class _FakeTextBox:
    """Fake LTTextBox for testing."""

    def __init__(self, bbox: tuple[float, ...], text: str) -> None:
        self.bbox = bbox
        self._text = text

    def get_text(self) -> str:
        return self._text


class _FakeFigure:
    """Fake LTFigure for testing."""

    def __init__(self, bbox: tuple[float, ...]) -> None:
        self.bbox = bbox


class _FakeImage:
    """Fake LTImage for testing."""

    def __init__(self, bbox: tuple[float, ...]) -> None:
        self.bbox = bbox


class _FakeOther:
    """Fake element that is neither text nor figure."""

    def __init__(self, bbox: tuple[float, ...]) -> None:
        self.bbox = bbox


class TestFlipBbox:
    def test_flips_y_coordinates(self):
        # pdfminer: bottom-left origin (x0=72, y0=600, x1=540, y1=700)
        # page_height=800 → top-left: (72, 100, 540, 200)
        result = _flip_bbox((72.0, 600.0, 540.0, 700.0), page_height=800.0)
        assert result == (72.0, 100.0, 540.0, 200.0)

    def test_zero_origin(self):
        result = _flip_bbox((0.0, 0.0, 100.0, 50.0), page_height=800.0)
        assert result == (0.0, 750.0, 100.0, 800.0)

    def test_full_page(self):
        result = _flip_bbox((0.0, 0.0, 612.0, 792.0), page_height=792.0)
        assert result == (0.0, 0.0, 612.0, 792.0)


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


class TestIsZeroArea:
    def test_zero_area_point(self):
        poly = [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        assert _is_zero_area(poly) is True

    def test_non_zero_area(self):
        poly = [0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]
        assert _is_zero_area(poly) is False


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
    def _make_lt_page(self, elements: list, height: float = 800.0) -> MagicMock:
        """Create a mock LTPage with height and iterable elements."""
        page = MagicMock()
        page.height = height
        page.__iter__ = MagicMock(return_value=iter(elements))
        return page

    def test_extracts_text_blocks(self):
        text_box = _FakeTextBox(bbox=(72.0, 600.0, 540.0, 700.0), text='한국어 문서 텍스트\n')
        lt_page = self._make_lt_page([text_box])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=2.0)

        assert len(result['layout_dets']) == 1
        el = result['layout_dets'][0]
        assert el['category_type'] == 'text_block'
        assert el['text'] == '한국어 문서 텍스트'
        assert el['anno_id'] == 0
        # bbox (72, 600, 540, 700) on page height 800
        # flipped: (72, 100, 540, 200), scaled 2x: (144, 200, 1080, 200, 1080, 400, 144, 400)
        assert el['poly'] == [144.0, 200.0, 1080.0, 200.0, 1080.0, 400.0, 144.0, 400.0]

    def test_extracts_figure_elements(self):
        figure = _FakeFigure(bbox=(50.0, 300.0, 300.0, 550.0))
        lt_page = self._make_lt_page([figure])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=2.0)

        assert len(result['layout_dets']) == 1
        el = result['layout_dets'][0]
        assert el['category_type'] == 'figure'
        assert el['anno_id'] == 0
        assert 'text' not in el

    def test_skips_empty_text_blocks(self):
        empty_box = _FakeTextBox(bbox=(0.0, 0.0, 100.0, 50.0), text='   \n')
        lt_page = self._make_lt_page([empty_box])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=2.0)

        assert len(result['layout_dets']) == 0

    def test_empty_page_returns_empty_layout(self):
        lt_page = self._make_lt_page([])

        with patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=2.0)

        assert result['layout_dets'] == []
        assert result['page_attribute'] == {}
        assert result['extra'] == {'relation': []}

    def test_assigns_sequential_anno_ids(self):
        box1 = _FakeTextBox(bbox=(0.0, 700.0, 100.0, 750.0), text='First\n')
        box2 = _FakeTextBox(bbox=(0.0, 500.0, 100.0, 600.0), text='Second\n')
        box3 = _FakeTextBox(bbox=(0.0, 300.0, 100.0, 400.0), text='Third\n')
        lt_page = self._make_lt_page([box1, box2, box3])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=1.0)

        ids = [el['anno_id'] for el in result['layout_dets']]
        assert ids == [0, 1, 2]

    def test_mixed_text_and_figure(self):
        text_box = _FakeTextBox(bbox=(72.0, 600.0, 540.0, 700.0), text='한국어 문서 텍스트\n')
        figure = _FakeFigure(bbox=(50.0, 300.0, 300.0, 550.0))
        lt_page = self._make_lt_page([text_box, figure])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=1.0)

        assert len(result['layout_dets']) == 2
        assert result['layout_dets'][0]['category_type'] == 'text_block'
        assert result['layout_dets'][1]['category_type'] == 'figure'

    def test_passes_page_number_to_extract_pages(self):
        lt_page = self._make_lt_page([])

        with patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])) as mock_extract:
            extract_page_elements(Path('/some/file.pdf'), page_no=5, scale=2.0)

        mock_extract.assert_called_once()
        call_kwargs = mock_extract.call_args
        assert call_kwargs[1]['page_numbers'] == [5]

    def test_coordinate_flip_correctness(self):
        """Verify bottom-left to top-left coordinate conversion."""
        # pdfminer bbox: (72, 600, 540, 700) on 800-height page
        # After flip: y0=800-700=100, y1=800-600=200
        # After 2x scale: (144, 200, 1080, 200, 1080, 400, 144, 400)
        box = _FakeTextBox(bbox=(72.0, 600.0, 540.0, 700.0), text='Test\n')
        lt_page = self._make_lt_page([box])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=2.0)

        poly = result['layout_dets'][0]['poly']
        # All coordinates should be non-negative
        assert all(v >= 0 for v in poly)
        # x1 >= x0
        assert poly[2] >= poly[0]
        # y1 >= y0
        assert poly[5] >= poly[1]
        # Expected values
        assert poly == [144.0, 200.0, 1080.0, 200.0, 1080.0, 400.0, 144.0, 400.0]

    def test_extracts_image_elements(self):
        """LTImage should be treated as figure category."""
        image = _FakeImage(bbox=(100.0, 200.0, 400.0, 500.0))
        lt_page = self._make_lt_page([image])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=1.0)

        assert len(result['layout_dets']) == 1
        assert result['layout_dets'][0]['category_type'] == 'figure'

    def test_skips_unknown_element_types(self):
        """Elements that are neither text nor figure should be ignored."""
        other = _FakeOther(bbox=(0.0, 0.0, 50.0, 50.0))
        lt_page = self._make_lt_page([other])

        with (
            patch(f'{_MODULE}.extract_pages', return_value=iter([lt_page])),
            patch(f'{_MODULE}.LTTextBox', new=_FakeTextBox),
            patch(f'{_MODULE}.LTFigure', new=_FakeFigure),
            patch(f'{_MODULE}.LTImage', new=_FakeImage),
        ):
            result = extract_page_elements(Path('/fake.pdf'), page_no=0, scale=1.0)

        assert len(result['layout_dets']) == 0
