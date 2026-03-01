"""Shared layout detection types.

Provides the LayoutRegion dataclass and LayoutDetector protocol
used by OCR pipeline engines.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class LayoutRegion:
    """A detected layout region from a layout detector.

    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2) pixel coordinates.
        category: OmniDocBench category type.
        score: Detection confidence score.
        text: Recognized text (optional, depends on detector).
    """

    bbox: tuple[float, float, float, float]
    category: str
    score: float
    text: str | None = None


class LayoutDetector(Protocol):
    """Protocol for layout detection backends.

    Implementations detect document layout regions (bounding boxes + categories)
    from page images.
    """

    def detect_layout(self, image_path: Path) -> list[LayoutRegion]:
        """Detect layout regions from a page image.

        Args:
            image_path: Path to the page image file.

        Returns:
            List of detected layout regions.
        """
        ...
