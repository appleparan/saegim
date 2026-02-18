"""Celery task for 2-stage OCR extraction (PP-StructureV3 + text OCR)."""

import json
import logging
from pathlib import Path
from typing import Any

import psycopg

from saegim.api.settings import get_settings
from saegim.services.ocr_pipeline import build_ocr_pipeline
from saegim.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    """Build psycopg DSN from settings.

    Returns:
        PostgreSQL connection string for psycopg.
    """
    settings = get_settings()
    return settings.database_url


def _update_page_extraction(
    dsn: str,
    page_id: str,
    auto_extracted_data: dict[str, Any],
) -> None:
    """Update a page's auto_extracted_data via sync psycopg.

    Args:
        dsn: PostgreSQL connection string.
        page_id: Page UUID string.
        auto_extracted_data: OmniDocBench dict to store.
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE pages
                SET auto_extracted_data = %s::jsonb, updated_at = NOW()
                WHERE id = %s::uuid
                """,
                (json.dumps(auto_extracted_data), page_id),
            )
        conn.commit()


def _update_document_status(dsn: str, document_id: str, status: str) -> None:
    """Update a document's status via sync psycopg.

    Args:
        dsn: PostgreSQL connection string.
        document_id: Document UUID string.
        status: New status value.
    """
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE documents SET status = %s WHERE id = %s::uuid',
                (status, document_id),
            )
        conn.commit()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_ocr_extraction(
    self: celery_app.Task,
    document_id: str,
    page_info: list[dict[str, Any]],
    ocr_config: dict[str, Any],
) -> dict[str, Any]:
    """Run 2-stage OCR extraction as a Celery task.

    Uses PP-StructureV3 for layout detection and a text OCR provider
    (Gemini, OlmOCR, or PP-OCR built-in) for text extraction.

    Args:
        self: Celery task instance (bound).
        document_id: Document UUID string.
        page_info: List of page info dicts with keys:
            - page_id: Page UUID string
            - page_idx: 0-based page index
            - width: Page image width in pixels
            - height: Page image height in pixels
            - image_path: Path to the page image file
        ocr_config: OCR provider configuration dict.

    Returns:
        Result dict with document_id, pages_processed, and status.

    Raises:
        Exception: Retried up to max_retries, then marks document
            as extraction_failed.
    """
    dsn = _get_dsn()
    ocr_provider_name = ocr_config.get('ocr_provider', 'unknown')

    logger.info(
        'Starting OCR extraction for document %s (%d pages, ocr=%s)',
        document_id,
        len(page_info),
        ocr_provider_name,
    )

    try:
        pipeline = build_ocr_pipeline(ocr_config)
        if pipeline is None:
            msg = 'Pipeline build returned None (pymupdf should not reach Celery task)'
            raise ValueError(msg)

        for page in page_info:
            page_id = page['page_id']
            page_idx = page['page_idx']
            image_path = Path(page['image_path'])
            width = page['width']
            height = page['height']

            logger.info(
                'Extracting page %s (idx=%d) with %s',
                page_id,
                page_idx,
                ocr_provider_name,
            )

            extracted = pipeline.extract_page(image_path, width, height)
            _update_page_extraction(dsn, page_id, extracted)

            logger.info(
                'Updated page %s (idx=%d) with %d elements',
                page_id,
                page_idx,
                len(extracted.get('layout_dets', [])),
            )

        _update_document_status(dsn, document_id, 'ready')
        logger.info('OCR extraction completed for document %s', document_id)

        return {
            'document_id': document_id,
            'pages_processed': len(page_info),
            'status': 'ready',
        }

    except Exception as exc:
        logger.exception('OCR extraction failed for document %s', document_id)

        if self.request.retries >= self.max_retries:
            try:
                _update_document_status(dsn, document_id, 'extraction_failed')
            except Exception:
                logger.exception(
                    'Failed to update document %s status to extraction_failed',
                    document_id,
                )
            raise

        raise self.retry(exc=exc) from exc
