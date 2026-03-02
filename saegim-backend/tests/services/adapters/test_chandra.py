"""Tests for ChandraAdapter."""

import json

from saegim.services.adapters.chandra import (
    ChandraAdapter,
    elements_to_page_ir,
    loads_lenient,
    parse_openai_response,
    strip_markdown_fences,
)
from saegim.services.docir import Geometry, PageIR


class TestChandraAdapterBuildMessages:
    def test_message_structure(self):
        adapter = ChandraAdapter()
        messages = adapter.build_messages(
            image_b64='abc123',
            mime_type='image/png',
            page_width=800,
            page_height=1200,
        )
        assert len(messages) == 1
        msg = messages[0]
        assert msg['role'] == 'user'
        assert len(msg['content']) == 2
        assert msg['content'][0]['type'] == 'text'
        assert '800' in msg['content'][0]['text']
        assert '1200' in msg['content'][0]['text']

    def test_image_url_format(self):
        adapter = ChandraAdapter()
        messages = adapter.build_messages(
            image_b64='AAAA',
            mime_type='image/jpeg',
            page_width=100,
            page_height=200,
        )
        image_part = messages[0]['content'][1]
        assert image_part['type'] == 'image_url'
        assert image_part['image_url']['url'] == 'data:image/jpeg;base64,AAAA'


class TestChandraAdapterParseResponse:
    def test_valid_response(self):
        adapter = ChandraAdapter()
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Hello', 'order': 0},
        ]
        result = {'choices': [{'message': {'content': json.dumps(elements)}}]}
        page_ir = adapter.parse_response(result, page_width=800, page_height=1200)

        assert isinstance(page_ir, PageIR)
        assert len(page_ir.elements) == 1
        assert page_ir.elements[0].kind == 'title'
        assert page_ir.elements[0].text == 'Hello'
        assert page_ir.width_px == 800
        assert page_ir.height_px == 1200

    def test_empty_response(self):
        adapter = ChandraAdapter()
        result = {'choices': []}
        page_ir = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page_ir.elements) == 0

    def test_invalid_json_response(self):
        adapter = ChandraAdapter()
        result = {'choices': [{'message': {'content': 'not json at all'}}]}
        page_ir = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page_ir.elements) == 0


class TestParseOpenaiResponse:
    def test_valid_response(self):
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Hello', 'order': 0},
        ]
        result = {'choices': [{'message': {'content': json.dumps(elements)}}]}
        parsed = parse_openai_response(result)
        assert len(parsed) == 1
        assert parsed[0]['category_type'] == 'title'

    def test_markdown_wrapped_response(self):
        elements = [
            {'category_type': 'text_block', 'bbox': [0, 0, 100, 50], 'text': 'Body', 'order': 0},
        ]
        text = f'```json\n{json.dumps(elements)}\n```'
        result = {'choices': [{'message': {'content': text}}]}
        parsed = parse_openai_response(result)
        assert len(parsed) == 1
        assert parsed[0]['category_type'] == 'text_block'

    def test_empty_choices(self):
        assert parse_openai_response({'choices': []}) == []

    def test_empty_content(self):
        assert parse_openai_response({'choices': [{'message': {'content': ''}}]}) == []

    def test_non_list_json(self):
        result = {'choices': [{'message': {'content': '{"key": "val"}'}}]}
        assert parse_openai_response(result) == []

    def test_empty_markdown_fence(self):
        result = {'choices': [{'message': {'content': '```json\n\n```'}}]}
        assert parse_openai_response(result) == []

    def test_invalid_escape_sequence(self):
        r"""Invalid escape sequences like \R should be repaired."""
        raw = (
            r'[{"category_type": "text_block",'
            r' "bbox": [0,0,100,50],'
            r' "text": "path\\Report",'
            r' "order": 0}]'
        )
        result = {'choices': [{'message': {'content': raw}}]}
        parsed = parse_openai_response(result)
        assert len(parsed) == 1
        assert parsed[0]['category_type'] == 'text_block'

    def test_missing_comma(self):
        raw = '[{"category_type": "title" "bbox": [0,0,100,50], "text": "Hi", "order": 0}]'
        result = {'choices': [{'message': {'content': raw}}]}
        parsed = parse_openai_response(result)
        assert len(parsed) >= 1

    def test_incomplete_json(self):
        raw = (
            '[{"category_type": "title",'
            ' "bbox": [0,0,100,50],'
            ' "text": "Hello", "order": 0},'
            ' {"category_type": "text_block"'
        )
        result = {'choices': [{'message': {'content': raw}}]}
        parsed = parse_openai_response(result)
        assert len(parsed) >= 1
        assert parsed[0]['category_type'] == 'title'


class TestStripMarkdownFences:
    def test_no_fences(self):
        assert strip_markdown_fences('[{"key": "val"}]') == '[{"key": "val"}]'

    def test_json_fence(self):
        text = '```json\n[{"key": "val"}]\n```'
        assert strip_markdown_fences(text) == '[{"key": "val"}]'

    def test_plain_fence(self):
        text = '```\n[{"key": "val"}]\n```'
        assert strip_markdown_fences(text) == '[{"key": "val"}]'

    def test_empty_fence(self):
        assert strip_markdown_fences('```json\n\n```').strip() == ''

    def test_unclosed_fence(self):
        text = '```json\n[{"key": "val"}]'
        assert strip_markdown_fences(text) == '[{"key": "val"}]'


class TestLoadsLenient:
    def test_valid_json(self):
        assert loads_lenient('[1, 2, 3]') == [1, 2, 3]

    def test_control_characters(self):
        result = loads_lenient('{"text": "line1\tline2"}')
        assert isinstance(result, dict)
        assert result['text'] == 'line1\tline2'

    def test_invalid_escape_repaired(self):
        raw = r'{"text": "C:\\Users\\Report"}'
        result = loads_lenient(raw)
        assert isinstance(result, dict)
        assert 'text' in result


class TestElementsToPageIr:
    def test_basic(self):
        elements = [
            {'category_type': 'title', 'bbox': [10, 20, 400, 60], 'text': 'Hello', 'order': 0},
            {'category_type': 'text_block', 'bbox': [10, 80, 400, 200], 'text': 'Body', 'order': 1},
        ]
        page = elements_to_page_ir(elements, 800, 1200)

        assert isinstance(page, PageIR)
        assert page.width_px == 800
        assert page.height_px == 1200
        assert len(page.elements) == 2
        assert page.elements[0].kind == 'title'
        assert page.elements[0].text == 'Hello'
        assert page.elements[0].geometry == Geometry(bbox=(10.0, 20.0, 400.0, 60.0))
        assert page.elements[0].reading_order == 0
        assert page.elements[1].kind == 'text_block'

    def test_empty_elements(self):
        page = elements_to_page_ir([], 800, 1200)
        assert len(page.elements) == 0

    def test_missing_bbox(self):
        elements = [{'category_type': 'text_block', 'text': 'No bbox', 'order': 0}]
        page = elements_to_page_ir(elements, 800, 1200)
        assert page.elements[0].geometry is None

    def test_missing_order_defaults_to_index(self):
        elements = [{'category_type': 'text_block', 'bbox': [0, 0, 100, 50]}]
        page = elements_to_page_ir(elements, 800, 1200)
        assert page.elements[0].reading_order == 0

    def test_bbox_converted_to_float(self):
        elements = [{'category_type': 'title', 'bbox': [10, 20, 300, 60], 'order': 0}]
        page = elements_to_page_ir(elements, 800, 1200)
        bbox = page.elements[0].geometry.bbox
        assert all(isinstance(v, float) for v in bbox)
