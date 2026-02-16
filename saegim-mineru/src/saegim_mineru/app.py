"""FastAPI application wrapping MinerU PDF extraction.

This service is AGPL-licensed due to the MinerU dependency and must be
deployed as a separate process/container from the main (Apache 2.0) app.
Communication happens via HTTP API using shared volume for PDF access.
"""

import copy
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

app = FastAPI(
    title='saegim-mineru',
    description='MinerU PDF extraction HTTP service',
    version='0.0.0',
)


class ExtractRequest(BaseModel):
    """Request body for PDF extraction."""

    pdf_path: str = Field(description='Path to PDF file (shared volume)')
    language: str = Field(default='korean', description='OCR language setting')
    backend: str = Field(default='pipeline', description='MinerU parsing backend')
    output_dir: str = Field(description='Output directory for images (shared volume)')


class ExtractResponse(BaseModel):
    """Response body containing MinerU content_list."""

    content_list: list[dict[str, Any]] = Field(description='MinerU content_list entries')


@app.get('/api/v1/health')
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {'status': 'ok'}


@app.post('/api/v1/extract')
def extract_pdf(request: ExtractRequest) -> ExtractResponse:
    """Extract structured layout elements from a PDF using MinerU.

    Args:
        request: Extraction parameters including PDF path and settings.

    Returns:
        MinerU content_list entries as JSON.

    Raises:
        HTTPException: If extraction fails or PDF file not found.
    """
    pdf_path = Path(request.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f'PDF not found: {request.pdf_path}')

    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        content_list = _run_mineru(
            pdf_path=pdf_path,
            language=request.language,
            backend=request.backend,
            output_dir=output_dir,
        )
        return ExtractResponse(content_list=content_list)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('MinerU extraction failed for %s', request.pdf_path)
        msg = f'Extraction failed: {exc}'
        raise HTTPException(status_code=500, detail=msg) from exc


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
    from mineru.cli.common import read_fn

    pdf_bytes = read_fn(str(pdf_path))
    pdf_file_name = pdf_path.stem

    if backend == 'pipeline':
        return _run_pipeline_backend(pdf_bytes, pdf_file_name, language, output_dir)
    elif backend.startswith('hybrid'):
        return _run_hybrid_backend(pdf_bytes, pdf_file_name, language, backend, output_dir)
    elif backend.startswith('vlm'):
        return _run_vlm_backend(pdf_bytes, pdf_file_name, backend, output_dir)
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

    parse_method = 'hybrid_auto'

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
