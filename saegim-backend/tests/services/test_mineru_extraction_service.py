"""Tests for MinerU extraction service."""

from unittest.mock import patch

import pytest

from saegim.services.mineru_extraction_service import (
    _bbox_to_poly,
    _build_element,
    _extract_caption_elements,
    _map_category_type,
    content_list_to_omnidocbench,
)


class TestMapCategoryType:
    """Tests for MinerU type → OmniDocBench category_type mapping."""

    def test_text_without_level_maps_to_text_block(self):
        assert _map_category_type({'type': 'text'}) == 'text_block'

    def test_text_with_level_zero_maps_to_text_block(self):
        assert _map_category_type({'type': 'text', 'text_level': 0}) == 'text_block'

    def test_text_with_level_one_maps_to_title(self):
        assert _map_category_type({'type': 'text', 'text_level': 1}) == 'title'

    def test_text_with_level_two_maps_to_title(self):
        assert _map_category_type({'type': 'text', 'text_level': 2}) == 'title'

    def test_image_maps_to_figure(self):
        assert _map_category_type({'type': 'image'}) == 'figure'

    def test_table_maps_to_table(self):
        assert _map_category_type({'type': 'table'}) == 'table'

    def test_equation_maps_to_equation_isolated(self):
        assert _map_category_type({'type': 'equation'}) == 'equation_isolated'

    def test_code_maps_to_code_txt(self):
        assert _map_category_type({'type': 'code'}) == 'code_txt'

    def test_list_maps_to_text_block(self):
        assert _map_category_type({'type': 'list'}) == 'text_block'

    def test_header_maps_to_header(self):
        assert _map_category_type({'type': 'header'}) == 'header'

    def test_footer_maps_to_footer(self):
        assert _map_category_type({'type': 'footer'}) == 'footer'

    def test_page_number_maps_to_page_number(self):
        assert _map_category_type({'type': 'page_number'}) == 'page_number'

    def test_unknown_type_maps_to_text_block(self):
        assert _map_category_type({'type': 'unknown_type'}) == 'text_block'

    def test_missing_type_maps_to_text_block(self):
        assert _map_category_type({}) == 'text_block'


class TestBboxToPoly:
    """Tests for 0-1000 normalized bbox → pixel coordinate polygon conversion."""

    def test_converts_full_page_bbox(self):
        poly = _bbox_to_poly([0, 0, 1000, 1000], width=2000, height=3000)
        assert poly == [0.0, 0.0, 2000.0, 0.0, 2000.0, 3000.0, 0.0, 3000.0]

    def test_converts_centered_bbox(self):
        poly = _bbox_to_poly([250, 250, 750, 750], width=2000, height=3000)
        assert poly == [500.0, 750.0, 1500.0, 750.0, 1500.0, 2250.0, 500.0, 2250.0]

    def test_converts_zero_bbox(self):
        poly = _bbox_to_poly([0, 0, 0, 0], width=2000, height=3000)
        assert poly == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def test_converts_with_unit_dimensions(self):
        poly = _bbox_to_poly([100, 200, 300, 400], width=1, height=1)
        assert poly == pytest.approx([0.1, 0.2, 0.3, 0.2, 0.3, 0.4, 0.1, 0.4])


class TestBuildElement:
    """Tests for OmniDocBench element construction."""

    def test_builds_text_element(self):
        element = _build_element('text_block', [0, 0, 10, 0, 10, 20, 0, 20], 0, text='Hello')
        assert element == {
            'category_type': 'text_block',
            'poly': [0, 0, 10, 0, 10, 20, 0, 20],
            'ignore': False,
            'order': 0,
            'anno_id': 0,
            'text': 'Hello',
        }

    def test_builds_figure_element_without_text(self):
        element = _build_element('figure', [0, 0, 10, 0, 10, 20, 0, 20], 1)
        assert 'text' not in element
        assert element['category_type'] == 'figure'
        assert element['anno_id'] == 1

    def test_builds_equation_element_with_latex(self):
        element = _build_element(
            'equation_isolated', [0, 0, 10, 0, 10, 20, 0, 20], 2, latex='E=mc^2'
        )
        assert element['latex'] == 'E=mc^2'
        assert 'text' not in element

    def test_builds_table_element_with_html(self):
        element = _build_element(
            'table', [0, 0, 10, 0, 10, 20, 0, 20], 3, html='<table><tr><td>A</td></tr></table>'
        )
        assert element['html'] == '<table><tr><td>A</td></tr></table>'


class TestExtractCaptionElements:
    """Tests for caption/footnote extraction from content_list items."""

    def test_extracts_image_caption(self):
        item = {'type': 'image', 'image_caption': ['Figure 1: Test image']}
        poly = [0, 0, 10, 0, 10, 20, 0, 20]
        captions = _extract_caption_elements(item, poly, 1, 'figure')
        assert len(captions) == 1
        assert captions[0]['category_type'] == 'figure_caption'
        assert captions[0]['text'] == 'Figure 1: Test image'
        assert captions[0]['anno_id'] == 1

    def test_extracts_table_caption_and_footnote(self):
        item = {
            'type': 'table',
            'table_caption': ['Table 1: Data'],
            'table_footnote': ['Note: values are approximate'],
        }
        poly = [0, 0, 10, 0, 10, 20, 0, 20]
        captions = _extract_caption_elements(item, poly, 5, 'table')
        assert len(captions) == 2
        assert captions[0]['category_type'] == 'table_caption'
        assert captions[1]['category_type'] == 'table_footnote'

    def test_skips_empty_captions(self):
        item = {'type': 'image', 'image_caption': []}
        poly = [0, 0, 10, 0, 10, 20, 0, 20]
        captions = _extract_caption_elements(item, poly, 1, 'figure')
        assert len(captions) == 0

    def test_skips_whitespace_captions(self):
        item = {'type': 'image', 'image_caption': ['  ', '\n']}
        poly = [0, 0, 10, 0, 10, 20, 0, 20]
        captions = _extract_caption_elements(item, poly, 1, 'figure')
        assert len(captions) == 0


class TestContentListToOmnidocbench:
    """Tests for full content_list → OmniDocBench conversion."""

    def test_converts_single_text_block(self):
        content_list = [
            {'type': 'text', 'text': 'Hello World', 'bbox': [0, 0, 500, 100], 'page_idx': 0},
        ]
        page_dims = {0: (2000, 3000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        assert 0 in result
        dets = result[0]['layout_dets']
        assert len(dets) == 1
        assert dets[0]['category_type'] == 'text_block'
        assert dets[0]['text'] == 'Hello World'
        assert dets[0]['anno_id'] == 0
        assert dets[0]['poly'] == pytest.approx([0.0, 0.0, 1000.0, 0.0, 1000.0, 300.0, 0.0, 300.0])

    def test_converts_title_with_text_level(self):
        content_list = [
            {
                'type': 'text',
                'text': 'Introduction',
                'text_level': 1,
                'bbox': [50, 50, 950, 100],
                'page_idx': 0,
            },
        ]
        page_dims = {0: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        dets = result[0]['layout_dets']
        assert dets[0]['category_type'] == 'title'
        assert dets[0]['text'] == 'Introduction'

    def test_converts_equation_with_latex(self):
        content_list = [
            {
                'type': 'equation',
                'text': '$$E=mc^2$$',
                'text_format': 'latex',
                'bbox': [100, 200, 900, 300],
                'page_idx': 0,
            },
        ]
        page_dims = {0: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        dets = result[0]['layout_dets']
        assert dets[0]['category_type'] == 'equation_isolated'
        assert dets[0]['latex'] == '$$E=mc^2$$'
        assert 'text' not in dets[0]

    def test_converts_table_with_html_and_caption(self):
        content_list = [
            {
                'type': 'table',
                'bbox': [50, 200, 950, 600],
                'page_idx': 0,
                'table_body': '<table><tr><td>A</td></tr></table>',
                'table_caption': ['Table 1: Results'],
                'table_footnote': [],
            },
        ]
        page_dims = {0: (2000, 3000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        dets = result[0]['layout_dets']
        # Table + caption = 2 elements
        assert len(dets) == 2
        assert dets[0]['category_type'] == 'table'
        assert dets[0]['html'] == '<table><tr><td>A</td></tr></table>'
        assert dets[1]['category_type'] == 'table_caption'
        assert dets[1]['text'] == 'Table 1: Results'

    def test_converts_image_with_caption(self):
        content_list = [
            {
                'type': 'image',
                'bbox': [100, 300, 900, 700],
                'page_idx': 0,
                'image_caption': ['Figure 1: Architecture'],
            },
        ]
        page_dims = {0: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        dets = result[0]['layout_dets']
        assert len(dets) == 2
        assert dets[0]['category_type'] == 'figure'
        assert dets[1]['category_type'] == 'figure_caption'

    def test_multi_page_content(self):
        content_list = [
            {'type': 'text', 'text': 'Page 1 text', 'bbox': [0, 0, 500, 100], 'page_idx': 0},
            {'type': 'text', 'text': 'Page 2 text', 'bbox': [0, 0, 500, 100], 'page_idx': 1},
        ]
        page_dims = {0: (1000, 1000), 1: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        assert len(result[0]['layout_dets']) == 1
        assert len(result[1]['layout_dets']) == 1
        assert result[0]['layout_dets'][0]['text'] == 'Page 1 text'
        assert result[1]['layout_dets'][0]['text'] == 'Page 2 text'

    def test_assigns_sequential_anno_ids_per_page(self):
        content_list = [
            {'type': 'text', 'text': 'A', 'bbox': [0, 0, 100, 50], 'page_idx': 0},
            {'type': 'text', 'text': 'B', 'bbox': [0, 50, 100, 100], 'page_idx': 0},
            {'type': 'text', 'text': 'C', 'bbox': [0, 0, 100, 50], 'page_idx': 1},
        ]
        page_dims = {0: (1000, 1000), 1: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        assert [d['anno_id'] for d in result[0]['layout_dets']] == [0, 1]
        assert [d['anno_id'] for d in result[1]['layout_dets']] == [0]

    def test_empty_content_list_returns_empty_pages(self):
        page_dims = {0: (1000, 1000)}
        result = content_list_to_omnidocbench([], page_dims)

        assert result[0] == {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }

    def test_returns_correct_structure(self):
        content_list = [
            {'type': 'text', 'text': 'Hello', 'bbox': [0, 0, 100, 100], 'page_idx': 0},
        ]
        page_dims = {0: (1000, 1000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        assert 'layout_dets' in result[0]
        assert 'page_attribute' in result[0]
        assert 'extra' in result[0]
        assert 'relation' in result[0]['extra']

    def test_mixed_element_types(self):
        content_list = [
            {
                'type': 'text',
                'text_level': 1,
                'text': 'Title',
                'bbox': [0, 0, 1000, 50],
                'page_idx': 0,
            },
            {'type': 'text', 'text': 'Body text', 'bbox': [0, 50, 1000, 200], 'page_idx': 0},
            {'type': 'image', 'bbox': [100, 200, 900, 500], 'page_idx': 0},
            {
                'type': 'equation',
                'text': '$$x^2$$',
                'text_format': 'latex',
                'bbox': [100, 500, 900, 600],
                'page_idx': 0,
            },
            {
                'type': 'table',
                'table_body': '<table></table>',
                'bbox': [0, 600, 1000, 900],
                'page_idx': 0,
            },
        ]
        page_dims = {0: (2000, 3000)}
        result = content_list_to_omnidocbench(content_list, page_dims)

        dets = result[0]['layout_dets']
        categories = [d['category_type'] for d in dets]
        assert 'title' in categories
        assert 'text_block' in categories
        assert 'figure' in categories
        assert 'equation_isolated' in categories
        assert 'table' in categories


class TestExtractDocument:
    """Tests for the top-level extract_document function."""

    @patch('saegim.services.mineru_extraction_service._call_mineru_api')
    def test_calls_mineru_api_and_converts(self, mock_api):
        mock_api.return_value = [
            {'type': 'text', 'text': 'Hello', 'bbox': [0, 0, 500, 100], 'page_idx': 0},
        ]
        from pathlib import Path

        from saegim.services.mineru_extraction_service import extract_document

        result = extract_document(
            pdf_path=Path('/tmp/test.pdf'),
            page_dimensions={0: (2000, 3000)},
        )

        mock_api.assert_called_once()
        assert 0 in result
        assert len(result[0]['layout_dets']) == 1

    @patch('saegim.services.mineru_extraction_service._call_mineru_api')
    def test_raises_on_mineru_api_failure(self, mock_api):
        mock_api.side_effect = RuntimeError('MinerU API request failed: connection refused')
        from pathlib import Path

        from saegim.services.mineru_extraction_service import extract_document

        with pytest.raises(RuntimeError, match='MinerU extraction failed'):
            extract_document(
                pdf_path=Path('/tmp/test.pdf'),
                page_dimensions={0: (1000, 1000)},
            )
