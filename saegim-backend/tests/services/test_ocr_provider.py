"""Tests for OCR provider utilities and prompts."""

from saegim.services.ocr_provider import (
    bbox_to_poly,
    build_omnidocbench_page,
    get_text_prompt,
)


class TestBboxToPoly:
    def test_basic_conversion(self):
        poly = bbox_to_poly([10, 20, 300, 400])
        assert poly == [10, 20, 300, 20, 300, 400, 10, 400]

    def test_zero_bbox(self):
        poly = bbox_to_poly([0, 0, 0, 0])
        assert poly == [0, 0, 0, 0, 0, 0, 0, 0]

    def test_float_coords(self):
        poly = bbox_to_poly([10.5, 20.3, 300.7, 400.9])
        assert poly == [10.5, 20.3, 300.7, 20.3, 300.7, 400.9, 10.5, 400.9]


class TestBuildOmnidocbenchPage:
    def test_build_with_elements(self):
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Title', 'order': 0},
            {
                'category_type': 'text_block',
                'bbox': [10, 80, 400, 200],
                'text': 'Body',
                'order': 1,
            },
        ]
        result = build_omnidocbench_page(elements)

        assert 'layout_dets' in result
        assert 'page_attribute' in result
        assert 'extra' in result
        assert len(result['layout_dets']) == 2
        assert result['layout_dets'][0]['anno_id'] == 0
        assert result['layout_dets'][1]['anno_id'] == 1
        assert result['layout_dets'][0]['text'] == 'Title'
        assert result['layout_dets'][0]['ignore'] is False

    def test_build_empty_elements(self):
        result = build_omnidocbench_page([])
        assert result['layout_dets'] == []
        assert result['page_attribute'] == {}
        assert result['extra'] == {'relation': []}

    def test_build_preserves_latex_html(self):
        elements = [
            {
                'category_type': 'equation_isolated',
                'bbox': [10, 20, 100, 50],
                'latex': 'E=mc^2',
                'order': 0,
            },
            {
                'category_type': 'table',
                'bbox': [10, 60, 400, 300],
                'html': '<table><tr><td>A</td></tr></table>',
                'order': 1,
            },
        ]
        result = build_omnidocbench_page(elements)
        assert result['layout_dets'][0]['latex'] == 'E=mc^2'
        assert 'text' not in result['layout_dets'][0]
        assert result['layout_dets'][1]['html'] == '<table><tr><td>A</td></tr></table>'


class TestGetTextPrompt:
    def test_default_prompt(self):
        prompt = get_text_prompt()
        assert 'Read all text' in prompt

    def test_table_prompt(self):
        prompt = get_text_prompt('table')
        assert 'markdown table' in prompt

    def test_equation_prompt(self):
        prompt = get_text_prompt('equation_isolated')
        assert 'LaTeX' in prompt

    def test_code_prompt(self):
        prompt = get_text_prompt('code_txt')
        assert 'source code' in prompt

    def test_unknown_category_returns_default(self):
        prompt = get_text_prompt('figure')
        assert 'Read all text' in prompt
