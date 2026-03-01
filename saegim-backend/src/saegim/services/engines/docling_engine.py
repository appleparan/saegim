"""Granite Docling 258M engine for document layout detection.

Uses IBM's granite-docling-258M vision-language model to detect text blocks,
tables, figures, equations, and other document elements from page images.
Outputs DocTags format which is parsed into OmniDocBench-compatible dicts.
"""

import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image

from saegim.services.engines.base import BaseOCREngine

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
    """
    values = _LOC_RE.findall(locs_str)
    return int(values[0]), int(values[1]), int(values[2]), int(values[3])


def _scale_to_poly(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    page_width: int,
    page_height: int,
) -> list[float]:
    """Convert DocTags 500x500 coordinates to pixel polygon.

    Args:
        x0: Left coordinate in 0-499 range.
        y0: Top coordinate in 0-499 range.
        x1: Right coordinate in 0-499 range.
        y1: Bottom coordinate in 0-499 range.
        page_width: Target page width in pixels.
        page_height: Target page height in pixels.

    Returns:
        8-element polygon [x0,y0, x1,y0, x1,y1, x0,y1] in pixel coordinates.
    """
    scale_x = page_width / _DOCTAGS_COORD_SIZE
    scale_y = page_height / _DOCTAGS_COORD_SIZE
    px0 = x0 * scale_x
    py0 = y0 * scale_y
    px1 = x1 * scale_x
    py1 = y1 * scale_y
    return [px0, py0, px1, py0, px1, py1, px0, py1]


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
    # Remove <otsl> and </otsl> tags
    content = otsl_content.replace('<otsl>', '').replace('</otsl>', '').strip()
    if not content:
        return '<table></table>'

    # Split into rows by <nl>
    row_strings = content.split('<nl>')
    rows: list[list[tuple[str, str]]] = []

    for row_str in row_strings:
        row_str = row_str.strip()
        if not row_str:
            continue
        cells: list[tuple[str, str]] = []
        # Split by cell tokens
        parts = re.split(r'(<fcel>|<ecel>|<lcel>|<ucel>|<xcel>)', row_str)
        current_type = ''
        for part in parts:
            part = part.strip()
            if part in ('<fcel>', '<ecel>', '<lcel>', '<ucel>', '<xcel>'):
                current_type = part
            elif current_type:
                cells.append((current_type, part))
                current_type = ''
            elif part and not current_type:
                # Content without a cell type prefix - skip
                pass
        # Handle trailing cell type with no content
        if current_type:
            cells.append((current_type, ''))
        rows.append(cells)

    if not rows:
        return '<table></table>'

    # Build span grid
    num_rows = len(rows)
    num_cols = max(len(row) for row in rows) if rows else 0
    if num_cols == 0:
        return '<table></table>'

    # Track which cells are covered by spans
    covered: set[tuple[int, int]] = set()
    # Build HTML
    html_rows: list[str] = []

    for r_idx, row in enumerate(rows):
        html_cells: list[str] = []
        for c_idx, (cell_type, cell_text) in enumerate(row):
            if (r_idx, c_idx) in covered:
                continue

            if cell_type == '<ecel>':
                html_cells.append('<td></td>')
            elif cell_type in ('<lcel>', '<ucel>', '<xcel>'):
                # These are span continuations, skip
                continue
            else:
                # <fcel> - calculate span
                colspan = 1
                rowspan = 1

                # Count horizontal span (lcel to the right)
                for nc in range(c_idx + 1, len(row)):
                    if row[nc][0] in ('<lcel>', '<xcel>'):
                        colspan += 1
                        covered.add((r_idx, nc))
                    else:
                        break

                # Count vertical span (ucel below)
                for nr in range(r_idx + 1, num_rows):
                    if nr < len(rows) and c_idx < len(rows[nr]):
                        if rows[nr][c_idx][0] in ('<ucel>', '<xcel>'):
                            rowspan += 1
                            covered.add((nr, c_idx))
                        else:
                            break
                    else:
                        break

                attrs = ''
                if colspan > 1:
                    attrs += f' colspan="{colspan}"'
                if rowspan > 1:
                    attrs += f' rowspan="{rowspan}"'

                html_cells.append(f'<td{attrs}>{cell_text}</td>')

        if html_cells:
            html_rows.append('<tr>' + ''.join(html_cells) + '</tr>')

    return '<table>' + ''.join(html_rows) + '</table>'


class DoclingEngine(BaseOCREngine):
    """Granite Docling 258M based document layout detection engine.

    Uses IBM's granite-docling-258M vision-language model for detecting
    text, tables, figures, equations, and other document layout elements.
    The model outputs DocTags format which is parsed into OmniDocBench dicts.

    Args:
        model_name: HuggingFace model identifier.
    """

    def __init__(self, model_name: str = 'ibm-granite/granite-docling-258M') -> None:
        self.model_name = model_name
        self._processor: Any = None
        self._model: Any = None
        self._device: str = 'cpu'

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
        self._ensure_model_loaded()
        image = Image.open(image_path)
        doctags = self._run_inference(image_path)
        return self._parse_doctags_to_elements(doctags, page_width, page_height, image)

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
            return (False, 'torch and transformers are required for DoclingEngine')

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return (True, f'DoclingEngine available (device: {device})')

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the model and processor on first use."""
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForVision2Seq, AutoProcessor

        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info('Loading DoclingEngine model %s on %s', self.model_name, self._device)

        self._processor = AutoProcessor.from_pretrained(self.model_name)
        self._model = AutoModelForVision2Seq.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16 if self._device == 'cuda' else torch.float32,
        ).to(self._device)

        logger.info('DoclingEngine model loaded successfully')

    def _run_inference(self, image_path: Path) -> str:
        """Run model inference on an image to produce DocTags.

        Args:
            image_path: Path to the page image file.

        Returns:
            DocTags string output from the model.
        """
        image = Image.open(image_path)

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

        # Strip EOS and padding tokens
        decoded = decoded.replace('<eos>', '').replace('<pad>', '').strip()
        return decoded

    def _parse_doctags_to_elements(
        self,
        doctags: str,
        page_width: int,
        page_height: int,
        image: Image.Image | None = None,
    ) -> dict[str, Any]:
        """Parse DocTags string into OmniDocBench-compatible elements.

        Args:
            doctags: DocTags markup string from model inference.
            page_width: Target page width in pixels.
            page_height: Target page height in pixels.
            image: Optional PIL Image (used for docling-core conversion if needed).

        Returns:
            OmniDocBench dict with layout_dets, page_attribute, extra.
        """
        elements: list[dict[str, Any]] = []
        anno_id = 0

        for match in _ELEMENT_RE.finditer(doctags):
            tag = match.group('tag')
            locs_str = match.group('locs')
            content = match.group('content').strip()

            category = _TAG_TO_CATEGORY.get(tag)
            if category is None:
                continue

            x0, y0, x1, y1 = _extract_locs(locs_str)
            poly = _scale_to_poly(x0, y0, x1, y1, page_width, page_height)

            element: dict[str, Any] = {
                'anno_id': anno_id,
                'category_type': category,
                'poly': poly,
            }

            if category == 'table':
                element['html'] = _otsl_to_html(content)
                # Extract plain text from table cells
                cell_texts = re.findall(r'<fcel>(.*?)(?=<[a-z])', content)
                element['text'] = ' '.join(t.strip() for t in cell_texts if t.strip())
            elif category == 'figure':
                element['text'] = ''
            else:
                element['text'] = content

            elements.append(element)
            anno_id += 1

        return {
            'layout_dets': elements,
            'page_attribute': {},
            'extra': {'relation': []},
        }
