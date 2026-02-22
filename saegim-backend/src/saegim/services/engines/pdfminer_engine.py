"""Pdfminer fallback engine (Type 4).

pdfminer.six extracts text directly from PDF pages using layout analysis,
not from rendered images. This engine exists for type consistency and
connection testing. The actual extraction is handled synchronously in
document_service.py via extraction_service.extract_page_elements().
"""

from pathlib import Path
from typing import Any

from saegim.services.engines.base import BaseOCREngine


class PdfminerEngine(BaseOCREngine):
    """Fallback OCR engine using pdfminer.six.

    This engine does not support image-based extraction. pdfminer works
    directly with PDF files during the synchronous upload path.
    The extract_page() method raises NotImplementedError because it is
    never called in the asyncio background extraction path.
    """

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Not supported: pdfminer uses PDF files directly.

        Args:
            image_path: Unused.
            page_width: Unused.
            page_height: Unused.

        Raises:
            NotImplementedError: Always. pdfminer extraction runs
                synchronously via extraction_service, not this method.
        """
        msg = (
            'PdfminerEngine does not support image-based extraction. '
            'Use extraction_service.extract_page_elements() with a PDF file path.'
        )
        raise NotImplementedError(msg)

    def test_connection(self) -> tuple[bool, str]:
        """Pdfminer requires no external services.

        Returns:
            Tuple of (True, success message).
        """
        return (True, 'pdfminer: no external service required')
