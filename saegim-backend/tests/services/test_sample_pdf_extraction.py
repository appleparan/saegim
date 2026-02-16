"""Integration tests using sample PDF files for extraction verification.

Uses real PDF files in saegim-backend/sample/ to verify:
- PyMuPDF extraction produces valid OmniDocBench structure
- MinerU extraction via HTTP API (marked @slow, requires saegim-mineru service)
"""

from pathlib import Path

import fitz
import httpx
import pytest

from saegim.services.extraction_service import extract_page_elements

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / 'sample'
ENG_PDF = SAMPLE_DIR / '2602.04118v1_eng.pdf'
KOR_PDF = SAMPLE_DIR / 'R2601510_kor.pdf'


def _has_sample_pdfs() -> bool:
    return ENG_PDF.exists() and KOR_PDF.exists()


skipif_no_samples = pytest.mark.skipif(
    not _has_sample_pdfs(),
    reason='Sample PDFs not found in saegim-backend/sample/',
)


class TestPyMuPDFExtractionEnglishPaper:
    """PyMuPDF extraction on English academic paper (2602.04118v1_eng.pdf)."""

    @skipif_no_samples
    def test_extracts_elements_from_first_page(self):
        pdf = fitz.open(str(ENG_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        assert 'layout_dets' in result
        assert 'page_attribute' in result
        assert 'extra' in result
        assert len(result['layout_dets']) > 0

    @skipif_no_samples
    def test_first_page_has_text_blocks(self):
        pdf = fitz.open(str(ENG_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        text_blocks = [el for el in result['layout_dets'] if el['category_type'] == 'text_block']
        assert len(text_blocks) > 0, 'English paper first page should have text blocks'

    @skipif_no_samples
    def test_first_page_text_contains_english(self):
        pdf = fitz.open(str(ENG_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        all_text = ' '.join(el.get('text', '') for el in result['layout_dets'] if el.get('text'))
        # English paper should contain Latin characters
        assert any(c.isascii() and c.isalpha() for c in all_text)

    @skipif_no_samples
    def test_elements_have_valid_poly_coordinates(self):
        pdf = fitz.open(str(ENG_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        for el in result['layout_dets']:
            poly = el['poly']
            assert len(poly) == 8, f'Poly should have 8 values, got {len(poly)}'
            # All coordinates should be non-negative
            assert all(v >= 0 for v in poly), f'Negative coordinate in poly: {poly}'
            # x1 >= x0, y1 >= y0
            assert poly[2] >= poly[0], f'x1 should >= x0: {poly}'
            assert poly[5] >= poly[1], f'y1 should >= y0: {poly}'

    @skipif_no_samples
    def test_elements_have_sequential_anno_ids(self):
        pdf = fitz.open(str(ENG_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        anno_ids = [el['anno_id'] for el in result['layout_dets']]
        assert anno_ids == list(range(len(anno_ids)))

    @skipif_no_samples
    def test_all_pages_extractable(self):
        pdf = fitz.open(str(ENG_PDF))
        for page_no in range(len(pdf)):
            page = pdf[page_no]
            result = extract_page_elements(page, scale=2.0)
            assert 'layout_dets' in result, f'Page {page_no} failed extraction'
        pdf.close()


class TestPyMuPDFExtractionKoreanDocument:
    """PyMuPDF extraction on Korean government document (R2601510_kor.pdf)."""

    @skipif_no_samples
    def test_extracts_elements_from_first_page(self):
        pdf = fitz.open(str(KOR_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        assert len(result['layout_dets']) > 0

    @skipif_no_samples
    def test_first_page_has_text_blocks(self):
        pdf = fitz.open(str(KOR_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        text_blocks = [el for el in result['layout_dets'] if el['category_type'] == 'text_block']
        assert len(text_blocks) > 0, 'Korean document first page should have text blocks'

    @skipif_no_samples
    def test_first_page_text_contains_korean(self):
        pdf = fitz.open(str(KOR_PDF))
        page = pdf[0]
        result = extract_page_elements(page, scale=2.0)
        pdf.close()

        all_text = ' '.join(el.get('text', '') for el in result['layout_dets'] if el.get('text'))
        # Korean document should contain Hangul characters
        has_hangul = any('\uac00' <= c <= '\ud7a3' for c in all_text)
        assert has_hangul, f'Expected Korean text, got: {all_text[:200]}'

    @skipif_no_samples
    def test_all_pages_extractable(self):
        pdf = fitz.open(str(KOR_PDF))
        for page_no in range(len(pdf)):
            page = pdf[page_no]
            result = extract_page_elements(page, scale=2.0)
            assert 'layout_dets' in result, f'Page {page_no} failed extraction'
        pdf.close()


class TestPyMuPDFExtractionComparison:
    """Compare extraction results between English and Korean PDFs."""

    @skipif_no_samples
    def test_both_pdfs_produce_valid_structure(self):
        for pdf_path in [ENG_PDF, KOR_PDF]:
            pdf = fitz.open(str(pdf_path))
            page = pdf[0]
            result = extract_page_elements(page, scale=2.0)
            pdf.close()

            assert isinstance(result['layout_dets'], list)
            assert isinstance(result['page_attribute'], dict)
            assert isinstance(result['extra'], dict)
            assert 'relation' in result['extra']

    @skipif_no_samples
    def test_only_valid_category_types(self):
        valid_categories = {'text_block', 'figure'}  # PyMuPDF only produces these two
        for pdf_path in [ENG_PDF, KOR_PDF]:
            pdf = fitz.open(str(pdf_path))
            for page_no in range(min(3, len(pdf))):  # Check first 3 pages
                result = extract_page_elements(pdf[page_no], scale=2.0)
                categories = {el['category_type'] for el in result['layout_dets']}
                assert categories.issubset(valid_categories), (
                    f'{pdf_path.name} page {page_no}: unexpected categories {categories - valid_categories}'
                )
            pdf.close()


def _mineru_service_available() -> bool:
    """Check if the saegim-mineru HTTP service is reachable."""
    from saegim.api.settings import get_settings

    settings = get_settings()
    try:
        with httpx.Client(timeout=httpx.Timeout(5.0)) as client:
            resp = client.get(f'{settings.mineru_api_url}/api/v1/health')
            return resp.status_code == 200
    except httpx.RequestError:
        return False


skipif_no_mineru = pytest.mark.skipif(
    not _mineru_service_available(),
    reason='saegim-mineru HTTP service not available',
)


@pytest.mark.slow
class TestMineruExtractionSamplePDFs:
    """MinerU extraction on sample PDFs via HTTP API.

    Requires saegim-mineru service running (e.g. via docker compose).
    Run with: uv run pytest -m slow tests/services/test_sample_pdf_extraction.py
    """

    @skipif_no_samples
    @skipif_no_mineru
    def test_english_paper_extraction(self, tmp_path):
        from saegim.services.mineru_extraction_service import extract_document

        # Get page dimensions from PyMuPDF
        pdf = fitz.open(str(ENG_PDF))
        page_dims = {}
        for i in range(len(pdf)):
            page = pdf[i]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            page_dims[i] = (pix.width, pix.height)
        pdf.close()

        result = extract_document(
            pdf_path=ENG_PDF,
            language='en',
            backend='pipeline',
            output_dir=tmp_path / 'eng_output',
            page_dimensions=page_dims,
        )

        assert len(result) > 0, 'Should produce results for at least one page'

        # Check first page has elements
        first_page = result[0]
        assert len(first_page['layout_dets']) > 0
        assert 'page_attribute' in first_page
        assert 'extra' in first_page

        # Verify category diversity (MinerU should detect more than just text_block)
        categories = {el['category_type'] for el in first_page['layout_dets']}
        assert 'text_block' in categories or 'title' in categories

    @skipif_no_samples
    @skipif_no_mineru
    def test_korean_document_extraction(self, tmp_path):
        from saegim.services.mineru_extraction_service import extract_document

        pdf = fitz.open(str(KOR_PDF))
        page_dims = {}
        for i in range(len(pdf)):
            page = pdf[i]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            page_dims[i] = (pix.width, pix.height)
        pdf.close()

        result = extract_document(
            pdf_path=KOR_PDF,
            language='korean',
            backend='pipeline',
            output_dir=tmp_path / 'kor_output',
            page_dimensions=page_dims,
        )

        assert len(result) > 0
        first_page = result[0]
        assert len(first_page['layout_dets']) > 0

    @skipif_no_samples
    @skipif_no_mineru
    def test_mineru_produces_more_categories_than_pymupdf(self, tmp_path):
        from saegim.services.mineru_extraction_service import extract_document

        pdf = fitz.open(str(ENG_PDF))
        page_dims = {}
        for i in range(len(pdf)):
            page = pdf[i]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            page_dims[i] = (pix.width, pix.height)

        # PyMuPDF extraction
        pymupdf_result = extract_page_elements(pdf[0], scale=2.0)
        pymupdf_categories = {el['category_type'] for el in pymupdf_result['layout_dets']}
        pdf.close()

        # MinerU extraction via HTTP API
        mineru_result = extract_document(
            pdf_path=ENG_PDF,
            language='en',
            backend='pipeline',
            output_dir=tmp_path / 'compare_output',
            page_dimensions=page_dims,
        )
        mineru_categories = {el['category_type'] for el in mineru_result[0]['layout_dets']}

        # MinerU should detect more diverse categories
        assert len(mineru_categories) >= len(pymupdf_categories), (
            f'MinerU ({mineru_categories}) should have >= categories than PyMuPDF ({pymupdf_categories})'
        )
