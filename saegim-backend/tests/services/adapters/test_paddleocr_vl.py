"""Tests for PaddleOcrVlAdapter."""

from saegim.services.adapters.paddleocr_vl import (
    PaddleOcrVlAdapter,
    _extract_content,
    _parse_paddleocr_output,
)
from saegim.services.docir import PageIR


class TestBuildMessages:
    def test_message_structure(self):
        adapter = PaddleOcrVlAdapter()
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
        assert msg['content'][0]['text'] == 'OCR:'
        assert msg['content'][1]['type'] == 'image_url'

    def test_image_url_format(self):
        adapter = PaddleOcrVlAdapter()
        messages = adapter.build_messages(
            image_b64='AAAA',
            mime_type='image/jpeg',
            page_width=100,
            page_height=200,
        )
        image_part = messages[0]['content'][1]
        assert image_part['image_url']['url'] == 'data:image/jpeg;base64,AAAA'

    def test_custom_prompt(self):
        adapter = PaddleOcrVlAdapter(prompt='Table Recognition:')
        messages = adapter.build_messages(
            image_b64='xyz',
            mime_type='image/png',
            page_width=800,
            page_height=1200,
        )
        assert messages[0]['content'][0]['text'] == 'Table Recognition:'


class TestParseResponse:
    def test_text_response(self):
        adapter = PaddleOcrVlAdapter()
        raw_text = 'This is extracted text from the document.'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)

        assert isinstance(page, PageIR)
        assert page.width_px == 800
        assert page.height_px == 1200
        assert len(page.elements) == 1
        assert page.elements[0].kind == 'text_block'
        assert page.elements[0].text == raw_text
        assert page.elements[0].geometry is None

    def test_multiline_text(self):
        adapter = PaddleOcrVlAdapter()
        raw_text = 'First line.\nSecond line.\nThird line.'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)

        assert len(page.elements) == 1
        assert page.elements[0].text == raw_text

    def test_empty_response(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': [{'message': {'content': ''}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page.elements) == 0

    def test_whitespace_only_response(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': [{'message': {'content': '   \n  \n  '}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page.elements) == 0

    def test_empty_choices(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': []}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page.elements) == 0

    def test_no_geometry(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': [{'message': {'content': 'Some text.'}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        for elem in page.elements:
            assert elem.geometry is None

    def test_fulltext_in_meta(self):
        adapter = PaddleOcrVlAdapter()
        raw_text = 'Hello world.'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert page.meta['fulltext'] == raw_text

    def test_prompt_in_meta(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': [{'message': {'content': 'Some text.'}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert page.meta['prompt'] == 'OCR:'

    def test_custom_prompt_in_meta(self):
        adapter = PaddleOcrVlAdapter(prompt='Table Recognition:')
        result = {'choices': [{'message': {'content': 'Table data.'}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert page.meta['prompt'] == 'Table Recognition:'

    def test_reading_order(self):
        adapter = PaddleOcrVlAdapter()
        result = {'choices': [{'message': {'content': 'Text content.'}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert page.elements[0].reading_order == 0


class TestExtractContent:
    def test_normal_response(self):
        result = {'choices': [{'message': {'content': 'hello'}}]}
        assert _extract_content(result) == 'hello'

    def test_empty_choices(self):
        assert _extract_content({'choices': []}) == ''

    def test_no_choices_key(self):
        assert _extract_content({}) == ''

    def test_empty_content(self):
        result = {'choices': [{'message': {'content': ''}}]}
        assert _extract_content(result) == ''


class TestParsePaddleocrOutput:
    def test_empty_string(self):
        page = _parse_paddleocr_output('', 800, 1200, 'OCR:')
        assert len(page.elements) == 0

    def test_whitespace_only(self):
        page = _parse_paddleocr_output('   \n  \n  ', 800, 1200, 'OCR:')
        assert len(page.elements) == 0

    def test_single_text_element(self):
        page = _parse_paddleocr_output('Hello world.', 800, 1200, 'OCR:')
        assert len(page.elements) == 1
        assert page.elements[0].id == 'e0'
        assert page.elements[0].kind == 'text_block'
        assert page.elements[0].text == 'Hello world.'

    def test_page_dimensions(self):
        page = _parse_paddleocr_output('Text.', 1024, 768, 'OCR:')
        assert page.width_px == 1024
        assert page.height_px == 768
