"""Docling-based document layout detection service.

Uses IBM's granite-docling-258M vision-language model to detect text blocks,
tables, figures, equations, and other document elements from page images.
Outputs DocTags format which is parsed into LayoutRegion instances.
"""

import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image

from saegim.services.layout_types import LayoutRegion

logger = logging.getLogger(__name__)

# DocTags coordinate space is normalized to 500x500
_DOCTAGS_COORD_SIZE = 500

# Mapping from DocTags element tags to OmniDocBench category types
_TAG_TO_CATEGORY: dict[str, str] = {
    'text': 'text_block',
    'title': 'title',
    'section-header': 'text_block',
    'caption': 'text_block',
    'footnote': 'text_block',
    'page-header': 'text_block',
    'page-footer': 'text_block',
    'list-item': 'text_block',
    'paragraph': 'text_block',
    'reference': 'text_block',
    'code': 'text_block',
    'table': 'table',
    'picture': 'figure',
    'chart': 'figure',
    'formula': 'equation',
}

# Pattern to match DocTags elements: <tag><loc_X><loc_Y><loc_X2><loc_Y2>content</tag>
_ELEMENT_RE = re.compile(
    r'<(?P<tag>' + '|'.join(re.escape(t) for t in _TAG_TO_CATEGORY) + r')'
    r'>(?P<locs>(?:<loc_\d+>){4})'
    r'(?P<content>.*?)'
    r'</(?P=tag)>',
    re.DOTALL,
)

# Pattern to extract loc values
_LOC_RE = re.compile(r'<loc_(\d+)>')


def _extract_locs(locs_str: str) -> tuple[int, int, int, int]:
    """Extract four location values from DocTags loc tokens.

    Args:
        locs_str: String containing 4 <loc_N> tokens.

    Returns:
        Tuple of (x0, y0, x1, y1) in 0-499 range.

    Raises:
        ValueError: If the string does not contain exactly 4 loc values.
    """
    values = _LOC_RE.findall(locs_str)
    if len(values) != 4:
        msg = f'Expected 4 loc values, got {len(values)} in: {locs_str!r}'
        raise ValueError(msg)
    return int(values[0]), int(values[1]), int(values[2]), int(values[3])


def _scale_bbox(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    page_width: int,
    page_height: int,
) -> tuple[float, float, float, float]:
    """Convert DocTags 500x500 coordinates to pixel bbox.

    Args:
        x0: Left coordinate in 0-499 range.
        y0: Top coordinate in 0-499 range.
        x1: Right coordinate in 0-499 range.
        y1: Bottom coordinate in 0-499 range.
        page_width: Target page width in pixels (must be positive).
        page_height: Target page height in pixels (must be positive).

    Returns:
        (x0, y0, x1, y1) bbox in pixel coordinates.

    Raises:
        ValueError: If page dimensions are not positive.
    """
    if page_width <= 0 or page_height <= 0:
        msg = f'Page dimensions must be positive, got {page_width}x{page_height}'
        raise ValueError(msg)
    scale_x = page_width / _DOCTAGS_COORD_SIZE
    scale_y = page_height / _DOCTAGS_COORD_SIZE
    return (x0 * scale_x, y0 * scale_y, x1 * scale_x, y1 * scale_y)


def _otsl_to_html(otsl_content: str) -> str:
    """Convert OTSL (Optimized Table Structure Language) to HTML table.

    OTSL tokens:
        <fcel> - full cell (regular cell with content)
        <ecel> - empty cell
        <lcel> - left-looking cell (horizontal span from previous cell)
        <ucel> - up-looking cell (vertical span from cell above)
        <xcel> - cross cell (spans both directions)
        <nl>   - row terminator

    Args:
        otsl_content: OTSL markup string.

    Returns:
        HTML table string.
    """
    content = otsl_content.replace('<otsl>', '').replace('</otsl>', '').strip()
    if not content:
        return '<table></table>'

    row_strings = content.split('<nl>')
    rows: list[list[tuple[str, str]]] = []

    for row_str in row_strings:
        row_str = row_str.strip()
        if not row_str:
            continue
        cells: list[tuple[str, str]] = []
        parts = re.split(r'(<fcel>|<ecel>|<lcel>|<ucel>|<xcel>)', row_str)
        current_type = ''
        for part in parts:
            part = part.strip()
            if part in ('<fcel>', '<ecel>', '<lcel>', '<ucel>', '<xcel>'):
                current_type = part
            elif current_type:
                cells.append((current_type, part))
                current_type = ''
        if current_type:
            cells.append((current_type, ''))
        rows.append(cells)

    if not rows:
        return '<table></table>'

    num_rows = len(rows)
    num_cols = max(len(row) for row in rows) if rows else 0
    if num_cols == 0:
        return '<table></table>'

    covered: set[tuple[int, int]] = set()
    html_rows: list[str] = []

    for r_idx, row in enumerate(rows):
        html_cells: list[str] = []
        for c_idx, (cell_type, cell_text) in enumerate(row):
            if (r_idx, c_idx) in covered:
                continue

            if cell_type == '<ecel>':
                html_cells.append('<td></td>')
            elif cell_type in ('<lcel>', '<ucel>', '<xcel>'):
                continue
            else:
                colspan = 1
                rowspan = 1

                for nc in range(c_idx + 1, len(row)):
                    if row[nc][0] in ('<lcel>', '<xcel>'):
                        colspan += 1
                    else:
                        break

                for nr in range(r_idx + 1, num_rows):
                    if nr < len(rows) and c_idx < len(rows[nr]):
                        if rows[nr][c_idx][0] in ('<ucel>', '<xcel>'):
                            rowspan += 1
                        else:
                            break
                    else:
                        break

                for dr in range(rowspan):
                    for dc in range(colspan):
                        if dr == 0 and dc == 0:
                            continue
                        covered.add((r_idx + dr, c_idx + dc))

                attrs = ''
                if colspan > 1:
                    attrs += f' colspan="{colspan}"'
                if rowspan > 1:
                    attrs += f' rowspan="{rowspan}"'

                html_cells.append(f'<td{attrs}>{cell_text}</td>')

        if html_cells:
            html_rows.append('<tr>' + ''.join(html_cells) + '</tr>')

    return '<table>' + ''.join(html_rows) + '</table>'


def parse_doctags_to_regions(
    doctags: str,
    page_width: int,
    page_height: int,
) -> list[LayoutRegion]:
    """Parse DocTags string into LayoutRegion instances.

    Args:
        doctags: DocTags markup string from model inference.
        page_width: Target page width in pixels.
        page_height: Target page height in pixels.

    Returns:
        List of LayoutRegion instances with pixel-coordinate bboxes.
    """
    regions: list[LayoutRegion] = []

    for match in _ELEMENT_RE.finditer(doctags):
        tag = match.group('tag')
        locs_str = match.group('locs')
        content = match.group('content').strip()

        category = _TAG_TO_CATEGORY.get(tag)
        if category is None:
            continue

        x0, y0, x1, y1 = _extract_locs(locs_str)
        bbox = _scale_bbox(x0, y0, x1, y1, page_width, page_height)

        # Build text content
        text: str | None = None
        if category == 'table':
            text = _otsl_to_html(content)
        elif category == 'figure':
            text = None
        else:
            text = content if content else None

        regions.append(
            LayoutRegion(
                bbox=bbox,
                category=category,
                score=1.0,
                text=text,
            )
        )

    return regions


class DoclingLayoutDetector:
    """Granite Docling 258M based document layout detector.

    Uses IBM's granite-docling-258M vision-language model for detecting
    text, tables, figures, equations, and other document layout elements.
    Implements the LayoutDetector protocol.
    """

    def __init__(self, model_name: str = 'ibm-granite/granite-docling-258M') -> None:
        """Initialize DoclingLayoutDetector with the specified model.

        Args:
            model_name: HuggingFace model identifier.
        """
        self.model_name = model_name
        self._processor: Any = None
        self._model: Any = None
        self._device: str = 'cpu'

    def detect_layout(self, image_path: Path) -> list[LayoutRegion]:
        """Detect layout regions from a page image.

        Args:
            image_path: Path to the page image file.

        Returns:
            List of detected LayoutRegion instances.
        """
        self._ensure_model_loaded()

        image = Image.open(image_path)
        page_width, page_height = image.size

        doctags = self._run_inference(image)
        return parse_doctags_to_regions(doctags, page_width, page_height)

    def test_connection(self) -> tuple[bool, str]:
        """Test that torch and transformers are available.

        Returns:
            Tuple of (success, message).
        """
        try:
            import importlib

            torch = importlib.import_module('torch')
            importlib.import_module('transformers')
        except (ImportError, ModuleNotFoundError):
            return (False, 'torch and transformers are required for DoclingLayoutDetector')

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return (True, f'DoclingLayoutDetector available (device: {device})')

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the model and processor on first use.

        Raises:
            RuntimeError: If model loading fails.
        """
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor

            self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(
                'Loading DoclingLayoutDetector model %s on %s (CUDA available: %s)',
                self.model_name,
                self._device,
                torch.cuda.is_available(),
            )

            self._processor = AutoProcessor.from_pretrained(self.model_name)
            self._model = AutoModelForImageTextToText.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16 if self._device == 'cuda' else torch.float32,
            ).to(self._device)  # type: ignore[invalid-argument-type]

            logger.info('DoclingLayoutDetector model loaded successfully on %s', self._device)
        except ImportError as exc:
            msg = 'torch and transformers are required for DoclingLayoutDetector'
            raise ImportError(msg) from exc
        except Exception as exc:
            logger.exception('Failed to load DoclingLayoutDetector model %s', self.model_name)
            msg = f'Failed to load model {self.model_name}: {exc}'
            raise RuntimeError(msg) from exc

    def _run_inference(self, image: Image.Image) -> str:
        """Run model inference on an image to produce DocTags.

        Args:
            image: PIL Image of the page.

        Returns:
            DocTags string output from the model.
        """
        messages = [
            {
                'role': 'user',
                'content': [
                    {'type': 'image'},
                    {'type': 'text', 'text': 'Convert this page to docling.'},
                ],
            },
        ]

        prompt = self._processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self._processor(text=prompt, images=[image], return_tensors='pt').to(self._device)

        import torch

        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, max_new_tokens=8192)

        decoded = self._processor.batch_decode(
            generated_ids[:, inputs.input_ids.shape[1] :],
            skip_special_tokens=False,
        )[0]

        decoded = decoded.replace('<eos>', '').replace('<pad>', '').strip()
        return decoded
