"""Celery task for MinerU PDF extraction."""

import json
import logging
from pathlib import Path

import psycopg

from saegim.api.settings import get_settings
from saegim.services import mineru_extraction_service
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
    auto_extracted_data: dict,
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
                """
                UPDATE documents SET status = %s WHERE id = %s::uuid
                """,
                (status, document_id),
            )
        conn.commit()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_mineru_extraction(
    self,
    document_id: str,
    pdf_path: str,
    page_info: list[dict],
    language: str = 'korean',
    backend: str = 'pipeline',
) -> dict:
    """Run MinerU extraction as a Celery task.

    Extracts structured layout elements from a PDF using MinerU,
    converts to OmniDocBench format, and stores results in the database.

    Args:
        self: Celery task instance (bound).
        document_id: Document UUID string.
        pdf_path: Path to the PDF file on disk.
        page_info: List of page info dicts with keys:
            - page_id: Page UUID string
            - page_idx: 0-based page index
            - width: Page image width in pixels
            - height: Page image height in pixels
        language: MinerU OCR language (default 'korean').
        backend: MinerU parsing backend (default 'pipeline').

    Returns:
        Result dict with document_id and page count.

    Raises:
        Exception: Retried up to max_retries, then marks document as extraction_failed.
    """
    dsn = _get_dsn()
    pdf_file = Path(pdf_path)

    logger.info(
        'Starting MinerU extraction for document %s (%d pages, backend=%s)',
        document_id,
        len(page_info),
        backend,
    )

    try:
        # Build page dimensions mapping
        page_dimensions = {
            p['page_idx']: (p['width'], p['height'])
            for p in page_info
        }

        # Run MinerU extraction
        settings = get_settings()
        output_dir = Path(settings.storage_path) / 'mineru_output' / document_id
        results = mineru_extraction_service.extract_document(
            pdf_path=pdf_file,
            language=language,
            backend=backend,
            output_dir=output_dir,
            page_dimensions=page_dimensions,
        )

        # Update each page's auto_extracted_data
        for page in page_info:
            page_idx = page['page_idx']
            page_id = page['page_id']
            extracted = results.get(page_idx, {
                'layout_dets': [],
                'page_attribute': {},
                'extra': {'relation': []},
            })
            _update_page_extraction(dsn, page_id, extracted)
            logger.info(
                'Updated page %s (idx=%d) with %d elements',
                page_id,
                page_idx,
                len(extracted.get('layout_dets', [])),
            )

        # Mark document as ready
        _update_document_status(dsn, document_id, 'ready')
        logger.info('MinerU extraction completed for document %s', document_id)

        return {
            'document_id': document_id,
            'pages_processed': len(page_info),
            'status': 'ready',
        }

    except Exception as exc:
        logger.exception('MinerU extraction failed for document %s', document_id)

        if self.request.retries >= self.max_retries:
            # Final failure: mark document as extraction_failed
            try:
                _update_document_status(dsn, document_id, 'extraction_failed')
            except Exception:
                logger.exception(
                    'Failed to update document %s status to extraction_failed',
                    document_id,
                )
            raise

        # Retry
        raise self.retry(exc=exc)
