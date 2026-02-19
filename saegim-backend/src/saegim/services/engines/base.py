"""Base OCR engine abstract class.

All OCR engine implementations must inherit from BaseOCREngine
and implement extract_page() and test_connection().
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines.

    Each engine type encapsulates the logic for extracting structured
    layout elements from a page image and returning OmniDocBench-compatible
    dicts.
    """

    @abstractmethod
    def extract_page(
        self,
        image_path: Path,
        page_width: int,
        page_height: int,
    ) -> dict[str, Any]:
        """Extract structured layout elements from a page image.

        Args:
            image_path: Path to the page image file.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            OmniDocBench-compatible dict with layout_dets, page_attribute, extra.
        """

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test connectivity to the engine's external services.

        Returns:
            Tuple of (success, message).
        """
