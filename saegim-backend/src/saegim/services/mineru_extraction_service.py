"""MinerU-based PDF extraction service for structured layout detection.

Wraps the MinerU Python API to extract text, images, tables, equations, and other
layout elements from PDF documents. Converts MinerU's content_list output to
OmniDocBench-compatible format for storage in pages.auto_extracted_data.
"""

import copy
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# MinerU type → OmniDocBench category_type mapping
_CATEGORY_MAP: dict[str, str] = {
    'text': 'text_block',
    'image': 'figure',
    'table': 'table',
    'equation': 'equation_isolated',
    'code': 'code_txt',
    'list': 'text_block',
    'header': 'header',
    'footer': 'footer',
    'page_number': 'page_number',
    'aside_text': 'abandon',
    'page_footnote': 'page_footnote',
}


def _map_category_type(item: dict[str, Any]) -> str:
    """Map MinerU content type to OmniDocBench category_type.

    Args:
        item: A MinerU content_list entry with 'type' and optional 'text_level'.

    Returns:
        OmniDocBench category_type string.
    """
    mineru_type = item.get('type', 'text')
    text_level = item.get('text_level', 0)

    # text with text_level >= 1 is a title/heading
    if mineru_type == 'text' and text_level and text_level >= 1:
        return 'title'

    return _CATEGORY_MAP.get(mineru_type, 'text_block')


def _bbox_to_poly(bbox: list[float], width: int, height: int) -> list[float]:
    """Convert MinerU 0-1000 normalized bbox to pixel coordinate polygon.

    Args:
        bbox: Bounding box [x0, y0, x1, y1] normalized to 0-1000 range.
        width: Page image width in pixels (2x rendered).
        height: Page image height in pixels (2x rendered).

    Returns:
        8-float polygon [x0,y0, x1,y0, x1,y1, x0,y1] in pixel coordinates.
    """
    x0 = bbox[0] / 1000.0 * width
    y0 = bbox[1] / 1000.0 * height
    x1 = bbox[2] / 1000.0 * width
    y1 = bbox[3] / 1000.0 * height
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _build_element(
    category_type: str,
    poly: list[float],
    anno_id: int,
    *,
    text: str | None = None,
    latex: str | None = None,
    html: str | None = None,
) -> dict[str, Any]:
    """Build an OmniDocBench layout element dict.

    Args:
        category_type: Element category (e.g. 'text_block', 'figure').
        poly: 8-float polygon in pixel coordinates.
        anno_id: Sequential annotation ID.
        text: Optional text content.
        latex: Optional LaTeX content (for equations).
        html: Optional HTML content (for tables).

    Returns:
        OmniDocBench-compatible layout element dict.
    """
    element: dict[str, Any] = {
        'category_type': category_type,
        'poly': poly,
        'ignore': False,
        'order': anno_id,
        'anno_id': anno_id,
    }
    if text is not None:
        element['text'] = text
    if latex is not None:
        element['latex'] = latex
    if html is not None:
        element['html'] = html
    return element


def _extract_caption_elements(
    item: dict[str, Any],
    poly: list[float],
    anno_id: int,
    category_prefix: str,
) -> list[dict[str, Any]]:
    """Extract caption and footnote sub-elements from a content_list item.

    Args:
        item: MinerU content_list entry (image or table type).
        poly: Parent element's polygon (used as fallback for captions).
        anno_id: Starting annotation ID for generated elements.
        category_prefix: 'figure' or 'table' to form caption category names.

    Returns:
        List of caption/footnote OmniDocBench elements.
    """
    elements: list[dict[str, Any]] = []

    caption_key = f'{category_prefix}_caption' if category_prefix == 'table' else 'image_caption'
    footnote_key = f'{category_prefix}_footnote' if category_prefix == 'table' else None

    captions = item.get(caption_key, [])
    if captions:
        caption_text = '\n'.join(captions) if isinstance(captions, list) else str(captions)
        if caption_text.strip():
            elements.append(
                _build_element(
                    f'{category_prefix}_caption',
                    poly,
                    anno_id,
                    text=caption_text,
                )
            )
            anno_id += 1

    if footnote_key:
        footnotes = item.get(footnote_key, [])
        if footnotes:
            footnote_text = '\n'.join(footnotes) if isinstance(footnotes, list) else str(footnotes)
            if footnote_text.strip():
                elements.append(
                    _build_element(
                        f'{category_prefix}_footnote',
                        poly,
                        anno_id,
                        text=footnote_text,
                    )
                )

    return elements


def content_list_to_omnidocbench(
    content_list: list[dict[str, Any]],
    page_dimensions: dict[int, tuple[int, int]],
) -> dict[int, dict[str, Any]]:
    """Convert MinerU content_list to per-page OmniDocBench format.

    Args:
        content_list: MinerU content_list.json output (reading-order sorted).
        page_dimensions: Mapping of page_idx (0-based) to (width, height) in pixels.

    Returns:
        Mapping of page_idx to OmniDocBench dict with layout_dets, page_attribute, extra.
    """
    # Initialize result for all known pages
    result: dict[int, dict[str, Any]] = {}
    for page_idx in page_dimensions:
        result[page_idx] = {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }

    # Track per-page anno_id counters
    anno_counters: dict[int, int] = {idx: 0 for idx in page_dimensions}

    for item in content_list:
        page_idx = item.get('page_idx', 0)
        if page_idx not in page_dimensions:
            logger.warning('Skipping item with unknown page_idx=%d', page_idx)
            continue

        width, height = page_dimensions[page_idx]
        bbox = item.get('bbox', [0, 0, 0, 0])
        poly = _bbox_to_poly(bbox, width, height)
        category_type = _map_category_type(item)
        anno_id = anno_counters[page_idx]

        # Build the main element
        text = item.get('text')
        latex = None
        html = None

        if category_type == 'equation_isolated':
            # Equations have LaTeX in the text field with text_format="latex"
            if item.get('text_format') == 'latex':
                latex = text
                text = None

        if category_type == 'table':
            html = item.get('table_body')

        element = _build_element(category_type, poly, anno_id, text=text, latex=latex, html=html)
        result[page_idx]['layout_dets'].append(element)
        anno_counters[page_idx] += 1

        # Extract caption/footnote sub-elements for images and tables
        if category_type == 'figure':
            captions = _extract_caption_elements(
                item, poly, anno_counters[page_idx], 'figure'
            )
            for cap in captions:
                result[page_idx]['layout_dets'].append(cap)
                anno_counters[page_idx] += 1

        elif category_type == 'table':
            captions = _extract_caption_elements(
                item, poly, anno_counters[page_idx], 'table'
            )
            for cap in captions:
                result[page_idx]['layout_dets'].append(cap)
                anno_counters[page_idx] += 1

    return result


def extract_document(
    pdf_path: Path,
    language: str = 'korean',
    backend: str = 'pipeline',
    output_dir: Path | None = None,
    page_dimensions: dict[int, tuple[int, int]] | None = None,
) -> dict[int, dict[str, Any]]:
    """Extract structured layout elements from a PDF using MinerU.

    Runs MinerU's document analysis pipeline and converts the results to
    per-page OmniDocBench format.

    Args:
        pdf_path: Path to the PDF file.
        language: OCR language setting (default 'korean').
        backend: MinerU parsing backend ('pipeline', 'hybrid-auto-engine', etc.).
        output_dir: Directory for MinerU output files (images, etc.).
        page_dimensions: Mapping of page_idx (0-based) to (width, height) in pixels.
            Required for coordinate conversion.

    Returns:
        Mapping of page_idx (0-based) to OmniDocBench dict.

    Raises:
        RuntimeError: If MinerU extraction fails.
    """
    if output_dir is None:
        output_dir = pdf_path.parent / f'{pdf_path.stem}_mineru_output'
    output_dir.mkdir(parents=True, exist_ok=True)

    if page_dimensions is None:
        page_dimensions = {}

    try:
        content_list = _run_mineru(pdf_path, language, backend, output_dir)
    except Exception as exc:
        msg = f'MinerU extraction failed for {pdf_path}: {exc}'
        logger.exception(msg)
        raise RuntimeError(msg) from exc

    # If no page dimensions provided, infer from content_list
    if not page_dimensions:
        page_indices = {item.get('page_idx', 0) for item in content_list}
        # Use default dimensions (will be overridden by caller in production)
        page_dimensions = {idx: (1, 1) for idx in page_indices}
        logger.warning(
            'No page_dimensions provided; coordinates will not be properly scaled'
        )

    return content_list_to_omnidocbench(content_list, page_dimensions)


def _run_mineru(
    pdf_path: Path,
    language: str,
    backend: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Run MinerU extraction and return content_list.

    Args:
        pdf_path: Path to the PDF file.
        language: OCR language setting.
        backend: MinerU parsing backend name.
        output_dir: Directory for output files.

    Returns:
        content_list entries from MinerU.
    """
    from mineru.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2, prepare_env, read_fn
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.enum_class import MakeMode

    pdf_bytes = read_fn(str(pdf_path))
    pdf_file_name = pdf_path.stem

    if backend == 'pipeline':
        return _run_pipeline_backend(
            pdf_bytes, pdf_file_name, language, output_dir
        )
    elif backend.startswith('hybrid'):
        return _run_hybrid_backend(
            pdf_bytes, pdf_file_name, language, backend, output_dir
        )
    elif backend.startswith('vlm'):
        return _run_vlm_backend(
            pdf_bytes, pdf_file_name, backend, output_dir
        )
    else:
        msg = f"Unsupported MinerU backend: '{backend}'"
        raise ValueError(msg)


def _run_pipeline_backend(
    pdf_bytes: bytes,
    pdf_file_name: str,
    language: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Run MinerU pipeline backend extraction.

    Args:
        pdf_bytes: Raw PDF file bytes.
        pdf_file_name: PDF file name (without extension).
        language: OCR language setting.
        output_dir: Directory for output files.

    Returns:
        content_list entries from MinerU pipeline.
    """
    from mineru.backend.pipeline.model_json_to_middle_json import (
        result_to_middle_json as pipeline_result_to_middle_json,
    )
    from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
    from mineru.backend.pipeline.pipeline_middle_json_mkcontent import (
        union_make as pipeline_union_make,
    )
    from mineru.cli.common import prepare_env
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.enum_class import MakeMode

    infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = (
        pipeline_doc_analyze(
            [pdf_bytes],
            [language],
            parse_method='auto',
            formula_enable=True,
            table_enable=True,
        )
    )

    local_image_dir, _ = prepare_env(str(output_dir), pdf_file_name, 'auto')
    image_writer = FileBasedDataWriter(local_image_dir)

    model_list = copy.deepcopy(infer_results[0])
    middle_json = pipeline_result_to_middle_json(
        model_list,
        all_image_lists[0],
        all_pdf_docs[0],
        image_writer,
        lang_list[0],
        ocr_enabled_list[0],
        True,
    )

    image_dir = str(Path(local_image_dir).name)
    content_list = pipeline_union_make(
        middle_json['pdf_info'], MakeMode.CONTENT_LIST, image_dir
    )

    return content_list


def _run_hybrid_backend(
    pdf_bytes: bytes,
    pdf_file_name: str,
    language: str,
    backend: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Run MinerU hybrid backend extraction.

    Args:
        pdf_bytes: Raw PDF file bytes.
        pdf_file_name: PDF file name (without extension).
        language: OCR language setting.
        backend: Full backend name (e.g. 'hybrid-auto-engine').
        output_dir: Directory for output files.

    Returns:
        content_list entries from MinerU hybrid backend.
    """
    from mineru.backend.hybrid.hybrid_analyze import doc_analyze as hybrid_doc_analyze
    from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
    from mineru.cli.common import prepare_env
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.engine_utils import get_vlm_engine
    from mineru.utils.enum_class import MakeMode

    engine = backend.removeprefix('hybrid-')
    if engine == 'auto-engine':
        engine = get_vlm_engine(inference_engine='auto', is_async=False)

    parse_method = f'hybrid_auto'

    local_image_dir, _ = prepare_env(str(output_dir), pdf_file_name, parse_method)
    image_writer = FileBasedDataWriter(local_image_dir)

    middle_json, _infer_result, _vlm_ocr_enable = hybrid_doc_analyze(
        pdf_bytes,
        image_writer=image_writer,
        backend=engine,
        parse_method=parse_method,
        language=language,
        inline_formula_enable=True,
    )

    image_dir = str(Path(local_image_dir).name)
    content_list = vlm_union_make(
        middle_json['pdf_info'], MakeMode.CONTENT_LIST, image_dir
    )

    return content_list


def _run_vlm_backend(
    pdf_bytes: bytes,
    pdf_file_name: str,
    backend: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Run MinerU VLM backend extraction.

    Args:
        pdf_bytes: Raw PDF file bytes.
        pdf_file_name: PDF file name (without extension).
        backend: Full backend name (e.g. 'vlm-auto-engine').
        output_dir: Directory for output files.

    Returns:
        content_list entries from MinerU VLM backend.
    """
    from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
    from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
    from mineru.cli.common import prepare_env
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.engine_utils import get_vlm_engine
    from mineru.utils.enum_class import MakeMode

    engine = backend.removeprefix('vlm-')
    if engine == 'auto-engine':
        engine = get_vlm_engine(inference_engine='auto', is_async=False)

    parse_method = 'vlm'

    local_image_dir, _ = prepare_env(str(output_dir), pdf_file_name, parse_method)
    image_writer = FileBasedDataWriter(local_image_dir)

    middle_json, _infer_result = vlm_doc_analyze(
        pdf_bytes,
        image_writer=image_writer,
        backend=engine,
    )

    image_dir = str(Path(local_image_dir).name)
    content_list = vlm_union_make(
        middle_json['pdf_info'], MakeMode.CONTENT_LIST, image_dir
    )

    return content_list
