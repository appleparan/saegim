"""Tests for DoclingEngine.

Uses mocked model inference to test DocTags → OmniDocBench conversion.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.engines.base import BaseOCREngine
from saegim.services.engines.docling_engine import DoclingEngine


# -- Sample DocTags for testing --

DOCTAGS_TEXT_ONLY = (
    '<doctag><text><loc_50><loc_100><loc_400><loc_150>'
    'Hello world</text>'
    '<text><loc_50><loc_200><loc_400><loc_250>'
    'Second paragraph</text></doctag>'
)

DOCTAGS_WITH_TABLE = (
    '<doctag><text><loc_50><loc_50><loc_400><loc_100>'
    'Introduction</text>'
    '<table><loc_50><loc_150><loc_450><loc_350>'
    '<otsl><fcel>Name<fcel>Score<nl>'
    '<fcel>Alice<fcel>95<nl>'
    '</otsl></table></doctag>'
)

DOCTAGS_WITH_FIGURE = (
    '<doctag><text><loc_50><loc_50><loc_400><loc_100>'
    'Caption text</text>'
    '<picture><loc_100><loc_150><loc_400><loc_400>'
    '</picture></doctag>'
)

DOCTAGS_MIXED = (
    '<doctag><title><loc_100><loc_10><loc_400><loc_50>'
    'Document Title</title>'
    '<text><loc_50><loc_60><loc_450><loc_110>'
    'Some body text</text>'
    '<table><loc_50><loc_120><loc_450><loc_300>'
    '<otsl><fcel>A<fcel>B<nl>'
    '<fcel>1<fcel>2<nl>'
    '</otsl></table>'
    '<picture><loc_100><loc_310><loc_400><loc_450>'
    '</picture></doctag>'
)

DOCTAGS_SECTION_HEADER = (
    '<doctag><section-header><loc_50><loc_50><loc_400><loc_100>'
    'Methods</section-header>'
    '<text><loc_50><loc_110><loc_400><loc_200>'
    'We used the following approach.</text></doctag>'
)

DOCTAGS_FORMULA = (
    '<doctag><text><loc_50><loc_50><loc_400><loc_100>'
    'The equation is:</text>'
    '<formula><loc_100><loc_120><loc_350><loc_180>'
    'E = mc^2</formula></doctag>'
)


class TestDoclingEngineInit:
    def test_is_base_ocr_engine_subclass(self):
        engine = DoclingEngine()
        assert isinstance(engine, BaseOCREngine)

    def test_default_model_name(self):
        engine = DoclingEngine()
        assert engine.model_name == 'ibm-granite/granite-docling-258M'

    def test_custom_model_name(self):
        engine = DoclingEngine(model_name='custom/model')
        assert engine.model_name == 'custom/model'

    def test_model_not_loaded_on_init(self):
        engine = DoclingEngine()
        assert engine._model is None
        assert engine._processor is None


class TestDoclingEngineTestConnection:
    def test_connection_success_with_torch(self):
        engine = DoclingEngine()
        with (
            patch.dict('sys.modules', {'torch': MagicMock()}),
            patch.dict('sys.modules', {'transformers': MagicMock()}),
        ):
            success, message = engine.test_connection()
        assert success is True
        assert 'available' in message.lower()

    def test_connection_failure_no_torch(self):
        engine = DoclingEngine()
        with patch.dict('sys.modules', {'torch': None}):
            success, message = engine.test_connection()
        assert success is False
        assert 'torch' in message.lower()


class TestDocTagsParsing:
    """Test _parse_doctags_to_elements conversion."""

    def test_text_blocks_extracted(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        assert len(result['layout_dets']) == 2
        for el in result['layout_dets']:
            assert el['category_type'] == 'text_block'
        assert result['layout_dets'][0]['text'] == 'Hello world'
        assert result['layout_dets'][1]['text'] == 'Second paragraph'

    def test_table_extracted(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_WITH_TABLE,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        tables = [el for el in result['layout_dets'] if el['category_type'] == 'table']
        assert len(tables) == 1
        table = tables[0]
        assert 'html' in table
        assert '<table>' in table['html'].lower() or '<td>' in table['html'].lower()

    def test_figure_extracted(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_WITH_FIGURE,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        figures = [el for el in result['layout_dets'] if el['category_type'] == 'figure']
        assert len(figures) == 1

    def test_mixed_elements_sequential_anno_ids(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_MIXED,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        anno_ids = [el['anno_id'] for el in result['layout_dets']]
        assert anno_ids == list(range(len(anno_ids)))

    def test_mixed_elements_category_types(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_MIXED,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        categories = [el['category_type'] for el in result['layout_dets']]
        assert 'title' in categories
        assert 'text_block' in categories
        assert 'table' in categories
        assert 'figure' in categories

    def test_section_header_mapped_to_text_block(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_SECTION_HEADER,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        categories = [el['category_type'] for el in result['layout_dets']]
        # section-header maps to text_block (OmniDocBench compatibility)
        assert all(c == 'text_block' for c in categories)

    def test_formula_extracted(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_FORMULA,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        formulas = [el for el in result['layout_dets'] if el['category_type'] == 'equation']
        assert len(formulas) == 1
        assert formulas[0]['text'] == 'E = mc^2'


class TestCoordinateScaling:
    """Test 500x500 normalized coords → actual pixel scaling."""

    def test_coordinate_scaling_square(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        # First text: <loc_50><loc_100><loc_400><loc_150>
        # Scale: 1000/500 = 2.0 for both x and y
        poly = result['layout_dets'][0]['poly']
        assert len(poly) == 8
        # x0=50*2=100, y0=100*2=200, x1=400*2=800, y1=150*2=300
        expected = [100.0, 200.0, 800.0, 200.0, 800.0, 300.0, 100.0, 300.0]
        assert poly == pytest.approx(expected)

    def test_coordinate_scaling_rectangular(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1224,
            page_height=1584,
            image=None,
        )

        poly = result['layout_dets'][0]['poly']
        scale_x = 1224.0 / 500.0  # 2.448
        scale_y = 1584.0 / 500.0  # 3.168
        expected = [
            50 * scale_x, 100 * scale_y,
            400 * scale_x, 100 * scale_y,
            400 * scale_x, 150 * scale_y,
            50 * scale_x, 150 * scale_y,
        ]
        assert poly == pytest.approx(expected)

    def test_all_coordinates_non_negative(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_MIXED,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        for el in result['layout_dets']:
            assert all(v >= 0 for v in el['poly']), f'Negative coord: {el["poly"]}'


class TestOmniDocBenchStructure:
    """Test output structure matches OmniDocBench format."""

    def test_has_required_top_level_keys(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        assert 'layout_dets' in result
        assert 'page_attribute' in result
        assert 'extra' in result

    def test_page_attribute_structure(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        page_attr = result['page_attribute']
        assert isinstance(page_attr, dict)

    def test_extra_has_relation(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        assert 'relation' in result['extra']
        assert isinstance(result['extra']['relation'], list)

    def test_elements_have_required_fields(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_MIXED,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        required_fields = {'anno_id', 'category_type', 'poly'}
        for el in result['layout_dets']:
            assert required_fields.issubset(el.keys()), f'Missing fields in {el}'

    def test_text_elements_have_text_field(self):
        engine = DoclingEngine()
        result = engine._parse_doctags_to_elements(
            DOCTAGS_TEXT_ONLY,
            page_width=1000,
            page_height=1000,
            image=None,
        )

        for el in result['layout_dets']:
            if el['category_type'] in ('text_block', 'title'):
                assert 'text' in el


class TestExtractPage:
    """Test extract_page with mocked model inference."""

    @patch('saegim.services.engines.docling_engine.Image')
    @patch.object(DoclingEngine, '_run_inference', return_value=DOCTAGS_TEXT_ONLY)
    @patch.object(DoclingEngine, '_ensure_model_loaded')
    def test_extract_page_returns_omnidocbench(self, mock_load, mock_infer, mock_image):
        mock_image.open.return_value = MagicMock()
        engine = DoclingEngine()
        result = engine.extract_page(Path('/fake/image.png'), 1000, 1000)

        assert 'layout_dets' in result
        assert 'page_attribute' in result
        assert 'extra' in result
        assert len(result['layout_dets']) == 2

    @patch('saegim.services.engines.docling_engine.Image')
    @patch.object(DoclingEngine, '_run_inference', return_value=DOCTAGS_WITH_TABLE)
    @patch.object(DoclingEngine, '_ensure_model_loaded')
    def test_extract_page_detects_tables(self, mock_load, mock_infer, mock_image):
        mock_image.open.return_value = MagicMock()
        engine = DoclingEngine()
        result = engine.extract_page(Path('/fake/image.png'), 1000, 1000)

        tables = [el for el in result['layout_dets'] if el['category_type'] == 'table']
        assert len(tables) >= 1
