"""DocIR intermediate representation for OCR pipeline.

Provides the core data structures (PageIR, ElementIR, Geometry) used
as the intermediate representation between model-specific Adapters and
format-agnostic Exporters in the 3-stage OCR pipeline.

See docs/architecture/docir-architecture.md for the full specification.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

ElementKind = Literal[
    'text_block',
    'title',
    'table',
    'figure',
    'equation',
    'header',
    'footer',
    'page_number',
    'code',
    'reference',
    'caption',
    'footnote',
    'unknown',
]


@dataclass(frozen=True)
class Geometry:
    """Spatial location of a layout element.

    Coordinates are always in pixel space. Adapters must convert
    normalised coordinates (e.g. 0-1000) to pixels before constructing
    this object.

    Attributes:
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.
        polygon: Arbitrary polygon as list of (x, y) pairs.
        rotation: Clockwise rotation in degrees.
    """

    bbox: tuple[float, float, float, float] | None = None
    polygon: list[tuple[float, float]] | None = None
    rotation: float = 0.0


@dataclass(frozen=True)
class ElementIR:
    """A single layout element detected on a page.

    Attributes:
        id: Unique identifier within the page.
        kind: Element category. Known kinds are type-safe via ElementKind;
            custom model labels are also accepted as plain strings.
        geometry: Spatial location (None for text-only outputs).
        text: Recognised text content (None for layout-only models).
        reading_order: Reading order index (0-based).
        scores: Model confidence scores (e.g. {"det": 0.95}).
        tags: Model-specific metadata (e.g. {"model_label": "paragraph_title"}).
    """

    id: str
    kind: ElementKind | str
    geometry: Geometry | None = None
    text: str | None = None
    reading_order: int | None = None
    scores: dict[str, float] = field(default_factory=dict)
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageIR:
    """Intermediate representation of a single document page.

    Attributes:
        page_id: Page identifier.
        width_px: Rendered image width in pixels.
        height_px: Rendered image height in pixels.
        elements: Immutable tuple of detected layout elements.
        artifacts: Model-produced auxiliary data (e.g. embedded images).
        meta: Model name, inference parameters, runtime info.
    """

    page_id: str
    width_px: int
    height_px: int
    elements: tuple[ElementIR, ...] = ()
    artifacts: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecognitionResult:
    """Text recognition result for a single element (split pipeline).

    Used in the merge stage of SplitPipelineEngine to inject recognised
    text into layout-only ElementIR instances.

    Attributes:
        element_id: ID of the ElementIR to match.
        text: Extracted text content.
        category_hint: Hint for text format (e.g. 'table' → html, 'equation' → latex).
        confidence: Recognition confidence score.
    """

    element_id: str
    text: str
    category_hint: str
    confidence: float | None = None
