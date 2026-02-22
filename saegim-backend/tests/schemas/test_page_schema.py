"""Tests for PageResponse schema pdf_url computation."""

import datetime
import uuid

from saegim.schemas.page import PageResponse


def _make_page_response(**overrides: object) -> PageResponse:
    """Create a minimal PageResponse with defaults."""
    defaults: dict[str, object] = {
        'id': uuid.uuid4(),
        'document_id': uuid.uuid4(),
        'page_no': 1,
        'width': 1190,
        'height': 1684,
        'image_path': '/storage/images/abc123_p1.png',
        'annotation_data': {},
        'status': 'pending',
        'updated_at': datetime.datetime.now(tz=datetime.UTC),
    }
    defaults.update(overrides)
    return PageResponse.model_validate(defaults)


class TestPageResponseImageUrl:
    """Tests for image_url computation."""

    def test_computes_image_url_from_image_path(self):
        resp = _make_page_response(image_path='/some/dir/doc_p1.png')
        assert resp.image_url == '/storage/images/doc_p1.png'

    def test_preserves_explicit_image_url(self):
        resp = _make_page_response(
            image_path='/some/dir/doc_p1.png',
            image_url='/custom/url.png',
        )
        assert resp.image_url == '/custom/url.png'


class TestPageResponsePdfUrl:
    """Tests for pdf_url computation."""

    def test_computes_pdf_url_from_pdf_path(self):
        resp = _make_page_response(
            pdf_path='/storage/pdfs/abc123_doc.pdf',
        )
        assert resp.pdf_url == '/storage/pdfs/abc123_doc.pdf'

    def test_extracts_filename_from_nested_path(self):
        resp = _make_page_response(
            pdf_path='/home/user/storage/pdfs/my-doc.pdf',
        )
        assert resp.pdf_url == '/storage/pdfs/my-doc.pdf'

    def test_empty_pdf_url_when_pdf_path_is_none(self):
        resp = _make_page_response(pdf_path=None)
        assert resp.pdf_url == ''

    def test_empty_pdf_url_when_pdf_path_not_provided(self):
        resp = _make_page_response()
        assert resp.pdf_url == ''

    def test_preserves_explicit_pdf_url(self):
        resp = _make_page_response(
            pdf_path='/some/path/doc.pdf',
            pdf_url='/custom/pdf-url.pdf',
        )
        assert resp.pdf_url == '/custom/pdf-url.pdf'

    def test_both_urls_computed_together(self):
        resp = _make_page_response(
            image_path='/dir/img.png',
            pdf_path='/dir/doc.pdf',
        )
        assert resp.image_url == '/storage/images/img.png'
        assert resp.pdf_url == '/storage/pdfs/doc.pdf'
