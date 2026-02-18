"""Integration tests using sample PDF files for extraction verification.

Uses real PDF files in saegim-backend/sample/ to verify:
- PyMuPDF extraction produces valid OmniDocBench structure
"""

from pathlib import Path

import fitz
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
                unexpected = categories - valid_categories
                assert categories.issubset(valid_categories), (
                    f'{pdf_path.name} page {page_no}: unexpected categories {unexpected}'
                )
            pdf.close()
