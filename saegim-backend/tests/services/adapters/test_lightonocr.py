"""Tests for LightOnOcrAdapter."""

from saegim.services.adapters.lightonocr import (
    LightOnOcrAdapter,
    _extract_content,
    _normalize_to_pixel,
    _parse_lighton_output,
)
from saegim.services.docir import PageIR


class TestBuildMessages:
    def test_no_prompt_image_only(self):
        adapter = LightOnOcrAdapter()
        messages = adapter.build_messages(
            image_b64='abc123',
            mime_type='image/png',
            page_width=800,
            page_height=1200,
        )
        assert len(messages) == 1
        msg = messages[0]
        assert msg['role'] == 'user'
        assert len(msg['content']) == 1
        assert msg['content'][0]['type'] == 'image_url'

    def test_image_url_format(self):
        adapter = LightOnOcrAdapter()
        messages = adapter.build_messages(
            image_b64='AAAA',
            mime_type='image/jpeg',
            page_width=100,
            page_height=200,
        )
        image_part = messages[0]['content'][0]
        assert image_part['image_url']['url'] == 'data:image/jpeg;base64,AAAA'

    def test_no_text_content(self):
        adapter = LightOnOcrAdapter()
        messages = adapter.build_messages(
            image_b64='xyz',
            mime_type='image/png',
            page_width=800,
            page_height=1200,
        )
        content_types = [c['type'] for c in messages[0]['content']]
        assert 'text' not in content_types


class TestParseResponse:
    def test_text_and_image_mixed(self):
        adapter = LightOnOcrAdapter()
        raw_text = (
            'Some document text here.\n'
            'More text content.\n'
            '![image](image_0.png)120,50,850,400\n'
            'Additional text below.'
        )
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=1000, page_height=2000)

        assert isinstance(page, PageIR)
        assert page.width_px == 1000
        assert page.height_px == 2000
        assert len(page.elements) == 3

        # First text block
        assert page.elements[0].kind == 'text_block'
        assert page.elements[0].text == 'Some document text here.\nMore text content.'
        assert page.elements[0].geometry is None

        # Image element
        assert page.elements[1].kind == 'figure'
        assert page.elements[1].geometry is not None
        geometry = page.elements[1].geometry
        assert geometry.bbox is not None

        # Third text block
        assert page.elements[2].kind == 'text_block'
        assert page.elements[2].text == 'Additional text below.'

    def test_text_only(self):
        adapter = LightOnOcrAdapter()
        raw_text = 'Just some text.\nAnother line.'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)

        assert len(page.elements) == 1
        assert page.elements[0].kind == 'text_block'
        assert page.elements[0].text == 'Just some text.\nAnother line.'

    def test_image_only(self):
        adapter = LightOnOcrAdapter()
        raw_text = '![image](image_0.png)100,200,300,400'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=1000, page_height=2000)

        assert len(page.elements) == 1
        assert page.elements[0].kind == 'figure'
        assert page.elements[0].geometry is not None

    def test_empty_response(self):
        adapter = LightOnOcrAdapter()
        result = {'choices': [{'message': {'content': ''}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page.elements) == 0

    def test_empty_choices(self):
        adapter = LightOnOcrAdapter()
        result = {'choices': []}
        page = adapter.parse_response(result, page_width=800, page_height=1200)
        assert len(page.elements) == 0

    def test_fulltext_in_meta(self):
        adapter = LightOnOcrAdapter()
        raw_text = 'Hello world.\n![image](image_0.png)100,200,300,400'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=1000, page_height=2000)
        assert page.meta['fulltext'] == raw_text

    def test_consecutive_text_blocks_merged(self):
        adapter = LightOnOcrAdapter()
        raw_text = 'Line one.\nLine two.\nLine three.'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=800, page_height=1200)

        assert len(page.elements) == 1
        assert page.elements[0].text == 'Line one.\nLine two.\nLine three.'

    def test_multiple_images(self):
        adapter = LightOnOcrAdapter()
        raw_text = '![image](image_0.png)100,200,300,400\n![image](image_1.png)500,600,700,800'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=1000, page_height=2000)

        assert len(page.elements) == 2
        assert page.elements[0].kind == 'figure'
        assert page.elements[1].kind == 'figure'


class TestNormalizeToPixel:
    def test_origin(self):
        assert _normalize_to_pixel(0, 0, 1000, 2000) == (0.0, 0.0)

    def test_max_values(self):
        px, py = _normalize_to_pixel(1000, 1000, 1000, 2000)
        assert px == 1000.0
        assert py == 2000.0

    def test_mid_values(self):
        px, py = _normalize_to_pixel(500, 500, 1000, 2000)
        assert px == 500.0
        assert py == 1000.0

    def test_arbitrary_values(self):
        px, py = _normalize_to_pixel(120, 50, 1000, 2000)
        assert px == 120.0
        assert py == 100.0


class TestCoordinateConversion:
    def test_image_bbox_pixel_conversion(self):
        adapter = LightOnOcrAdapter()
        raw_text = '![image](image_0.png)120,50,850,400'
        result = {'choices': [{'message': {'content': raw_text}}]}
        page = adapter.parse_response(result, page_width=1000, page_height=2000)

        geometry = page.elements[0].geometry
        assert geometry is not None
        bbox = geometry.bbox
        assert bbox is not None
        # 120 * 1000 / 1000 = 120.0
        assert bbox[0] == 120.0
        # 50 * 2000 / 1000 = 100.0
        assert bbox[1] == 100.0
        # 850 * 1000 / 1000 = 850.0
        assert bbox[2] == 850.0
        # 400 * 2000 / 1000 = 800.0
        assert bbox[3] == 800.0


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


class TestParseLightonOutput:
    def test_empty_string(self):
        page = _parse_lighton_output('', 800, 1200)
        assert len(page.elements) == 0

    def test_whitespace_only(self):
        page = _parse_lighton_output('   \n  \n  ', 800, 1200)
        assert len(page.elements) == 0

    def test_reading_order_sequential(self):
        raw_text = 'First text.\n![image](image_0.png)100,200,300,400\nSecond text.'
        page = _parse_lighton_output(raw_text, 1000, 2000)
        assert len(page.elements) == 3
        assert page.elements[0].reading_order == 0
        assert page.elements[1].reading_order == 1
        assert page.elements[2].reading_order == 2
