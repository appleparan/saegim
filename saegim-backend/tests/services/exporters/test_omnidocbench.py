"""Tests for OmniDocBench exporter."""

from saegim.services.docir import ElementIR, Geometry, PageIR
from saegim.services.exporters.omnidocbench import bbox_to_poly, export_page


class TestBboxToPoly:
    def test_basic(self):
        assert bbox_to_poly((10.0, 20.0, 300.0, 400.0)) == [
            10.0,
            20.0,
            300.0,
            20.0,
            300.0,
            400.0,
            10.0,
            400.0,
        ]

    def test_zero(self):
        assert bbox_to_poly((0.0, 0.0, 0.0, 0.0)) == [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

    def test_float_coords(self):
        result = bbox_to_poly((10.5, 20.3, 300.7, 400.9))
        assert result == [10.5, 20.3, 300.7, 20.3, 300.7, 400.9, 10.5, 400.9]


class TestExportPage:
    def test_empty_page(self):
        page = PageIR(page_id='p0', width_px=800, height_px=1200)
        result = export_page(page)
        assert result == {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }

    def test_text_element(self):
        elem = ElementIR(
            id='e0',
            kind='text_block',
            geometry=Geometry(bbox=(50.0, 100.0, 500.0, 300.0)),
            text='Hello world',
            reading_order=0,
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        result = export_page(page)

        assert len(result['layout_dets']) == 1
        det = result['layout_dets'][0]
        assert det['category_type'] == 'text_block'
        assert det['poly'] == [50.0, 100.0, 500.0, 100.0, 500.0, 300.0, 50.0, 300.0]
        assert det['text'] == 'Hello world'
        assert det['order'] == 0
        assert det['anno_id'] == 0
        assert det['ignore'] is False

    def test_equation_uses_latex_field(self):
        elem = ElementIR(
            id='e0',
            kind='equation_isolated',
            geometry=Geometry(bbox=(10.0, 20.0, 100.0, 50.0)),
            text='E=mc^2',
            reading_order=0,
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        result = export_page(page)

        det = result['layout_dets'][0]
        assert det['latex'] == 'E=mc^2'
        assert 'text' not in det
        assert 'html' not in det

    def test_equation_kind_uses_latex_field(self):
        elem = ElementIR(
            id='e0',
            kind='equation',
            geometry=Geometry(bbox=(10.0, 20.0, 100.0, 50.0)),
            text='x^2+y^2=r^2',
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        det = export_page(page)['layout_dets'][0]
        assert det['latex'] == 'x^2+y^2=r^2'
        assert 'text' not in det

    def test_table_uses_html_field(self):
        elem = ElementIR(
            id='e0',
            kind='table',
            geometry=Geometry(bbox=(10.0, 60.0, 400.0, 300.0)),
            text='<table><tr><td>A</td></tr></table>',
            reading_order=1,
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        result = export_page(page)

        det = result['layout_dets'][0]
        assert det['html'] == '<table><tr><td>A</td></tr></table>'
        assert 'text' not in det
        assert 'latex' not in det

    def test_geometry_none_produces_zero_poly(self):
        elem = ElementIR(id='e0', kind='text_block', text='No bbox')
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        result = export_page(page)

        det = result['layout_dets'][0]
        assert det['poly'] == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def test_polygon_geometry(self):
        poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
        elem = ElementIR(
            id='e0',
            kind='figure',
            geometry=Geometry(polygon=poly),
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        result = export_page(page)

        det = result['layout_dets'][0]
        assert det['poly'] == [0.0, 0.0, 100.0, 0.0, 100.0, 50.0, 0.0, 50.0]

    def test_multiple_elements(self):
        e1 = ElementIR(
            id='e0',
            kind='title',
            geometry=Geometry(bbox=(10.0, 20.0, 400.0, 60.0)),
            text='Title',
            reading_order=0,
        )
        e2 = ElementIR(
            id='e1',
            kind='text_block',
            geometry=Geometry(bbox=(10.0, 80.0, 400.0, 200.0)),
            text='Body',
            reading_order=1,
        )
        page = PageIR(
            page_id='p0',
            width_px=800,
            height_px=1200,
            elements=(e1, e2),
        )
        result = export_page(page)

        assert len(result['layout_dets']) == 2
        assert result['layout_dets'][0]['anno_id'] == 0
        assert result['layout_dets'][1]['anno_id'] == 1
        assert result['layout_dets'][0]['text'] == 'Title'
        assert result['layout_dets'][1]['text'] == 'Body'

    def test_reading_order_fallback_to_index(self):
        elem = ElementIR(id='e0', kind='text_block', text='No order')
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        det = export_page(page)['layout_dets'][0]
        assert det['order'] == 0

    def test_no_text_produces_no_text_field(self):
        elem = ElementIR(
            id='e0',
            kind='figure',
            geometry=Geometry(bbox=(10.0, 20.0, 300.0, 400.0)),
        )
        page = PageIR(page_id='p0', width_px=800, height_px=1200, elements=(elem,))
        det = export_page(page)['layout_dets'][0]
        assert 'text' not in det
        assert 'latex' not in det
        assert 'html' not in det
