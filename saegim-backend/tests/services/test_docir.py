"""Tests for DocIR intermediate representation."""

import dataclasses

import pytest

from saegim.services.docir import (
    ElementIR,
    Geometry,
    PageIR,
    RecognitionResult,
)


class TestGeometry:
    def test_create_with_bbox(self):
        g = Geometry(bbox=(10.0, 20.0, 300.0, 400.0))
        assert g.bbox == (10.0, 20.0, 300.0, 400.0)
        assert g.polygon is None
        assert g.rotation == 0.0

    def test_create_with_polygon(self):
        poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
        g = Geometry(polygon=poly)
        assert g.bbox is None
        assert g.polygon == poly

    def test_defaults(self):
        g = Geometry()
        assert g.bbox is None
        assert g.polygon is None
        assert g.rotation == 0.0

    def test_frozen(self):
        g = Geometry(bbox=(0.0, 0.0, 1.0, 1.0))
        with pytest.raises(dataclasses.FrozenInstanceError):
            g.bbox = (1.0, 1.0, 2.0, 2.0)  # type: ignore[misc]


class TestElementIR:
    def test_create_minimal(self):
        e = ElementIR(id='e0', kind='text_block')
        assert e.id == 'e0'
        assert e.kind == 'text_block'
        assert e.geometry is None
        assert e.text is None
        assert e.reading_order is None
        assert e.scores == {}
        assert e.tags == {}

    def test_create_full(self):
        g = Geometry(bbox=(10.0, 20.0, 300.0, 400.0))
        e = ElementIR(
            id='e1',
            kind='title',
            geometry=g,
            text='Hello',
            reading_order=0,
            scores={'det': 0.95},
            tags={'model_label': 'document_title'},
        )
        assert e.geometry is not None
        assert e.geometry.bbox == (10.0, 20.0, 300.0, 400.0)
        assert e.text == 'Hello'
        assert e.reading_order == 0
        assert e.scores == {'det': 0.95}
        assert e.tags == {'model_label': 'document_title'}

    def test_custom_kind(self):
        e = ElementIR(id='e2', kind='custom_label')
        assert e.kind == 'custom_label'

    def test_frozen(self):
        e = ElementIR(id='e0', kind='text_block')
        with pytest.raises(dataclasses.FrozenInstanceError):
            e.text = 'modified'  # type: ignore[misc]


class TestPageIR:
    def test_create_empty(self):
        p = PageIR(page_id='p0', width_px=800, height_px=1200)
        assert p.page_id == 'p0'
        assert p.width_px == 800
        assert p.height_px == 1200
        assert p.elements == ()
        assert p.artifacts == {}
        assert p.meta == {}

    def test_create_with_elements(self):
        e1 = ElementIR(id='e0', kind='title', text='Title')
        e2 = ElementIR(id='e1', kind='text_block', text='Body')
        p = PageIR(
            page_id='p1',
            width_px=800,
            height_px=1200,
            elements=(e1, e2),
        )
        assert len(p.elements) == 2
        assert p.elements[0].text == 'Title'
        assert p.elements[1].text == 'Body'

    def test_elements_is_tuple(self):
        p = PageIR(page_id='p0', width_px=800, height_px=1200, elements=())
        assert isinstance(p.elements, tuple)

    def test_frozen(self):
        p = PageIR(page_id='p0', width_px=800, height_px=1200)
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.page_id = 'modified'  # type: ignore[misc]

    def test_meta_and_artifacts(self):
        p = PageIR(
            page_id='p0',
            width_px=800,
            height_px=1200,
            artifacts={'embedded_images': [b'img']},
            meta={'model_name': 'chandra'},
        )
        assert p.artifacts == {'embedded_images': [b'img']}
        assert p.meta == {'model_name': 'chandra'}


class TestRecognitionResult:
    def test_create(self):
        r = RecognitionResult(
            element_id='e0',
            text='Hello',
            category_hint='text_block',
        )
        assert r.element_id == 'e0'
        assert r.text == 'Hello'
        assert r.category_hint == 'text_block'
        assert r.confidence is None

    def test_with_confidence(self):
        r = RecognitionResult(
            element_id='e1',
            text='E=mc^2',
            category_hint='equation',
            confidence=0.92,
        )
        assert r.confidence == 0.92

    def test_frozen(self):
        r = RecognitionResult(element_id='e0', text='Hi', category_hint='text_block')
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.text = 'modified'  # type: ignore[misc]
