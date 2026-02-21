"""PyMuPDF fallback engine (Type 4).

PyMuPDF extracts text directly from PDF pages using fitz.Page objects,
not from rendered images. This engine exists for type consistency and
connection testing. The actual extraction is handled synchronously in
document_service.py via extraction_service.extract_page_elements().
"""

from pathlib import Path
from typing import Any

from saegim.services.engines.base import BaseOCREngine


class PyMuPDFEngine(BaseOCREngine):
    """Fallback OCR engine using PyMuPDF.

    This engine does not support image-based extraction. PyMuPDF works
    directly with fitz.Page objects during the synchronous upload path.
    The extract_page() method raises NotImplementedError because it is
    never called in the asyncio background extraction path.
    """

    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Not supported: PyMuPDF uses fitz.Page objects directly.

        Args:
            image_path: Unused.
            page_width: Unused.
            page_height: Unused.

        Raises:
            NotImplementedError: Always. PyMuPDF extraction runs
                synchronously via extraction_service, not this method.
        """
        msg = (
            'PyMuPDFEngine does not support image-based extraction. '
            'Use extraction_service.extract_page_elements() with a fitz.Page object.'
        )
        raise NotImplementedError(msg)

    def test_connection(self) -> tuple[bool, str]:
        """PyMuPDF requires no external services.

        Returns:
            Tuple of (True, success message).
        """
        return (True, 'PyMuPDF: no external service required')
