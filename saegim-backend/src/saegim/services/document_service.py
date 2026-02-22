"""Document service for PDF upload and image conversion."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

import asyncpg
import pypdfium2 as pdfium

from saegim.repositories import document_repo, page_repo, project_repo
from saegim.services import extraction_service
from saegim.services.engines import build_engine

logger = logging.getLogger(__name__)


async def upload_and_convert(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    filename: str,
    file_content: bytes,
    storage_path: str,
) -> dict:
    """Upload a PDF and convert each page to an image.

    Renders page images at 2x scale using pypdfium2. Extraction backend
    is determined by the project's ``engine_type`` setting.

    Engine types:
    - 'pdfminer' / 'pymupdf' (legacy): Synchronous extraction via pdfminer.six
    - Others: Background asyncio task for OCR extraction

    Args:
        pool: Database connection pool.
        project_id: Parent project UUID.
        filename: Original PDF filename.
        file_content: Raw PDF bytes.
        storage_path: Base storage directory path.

    Returns:
        dict: Document info with id, filename, total_pages, status.
    """
    storage = Path(storage_path)
    pdfs_dir = storage / 'pdfs'
    images_dir = storage / 'images'
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Resolve extraction engine from project config
    ocr_config = await _resolve_ocr_config(pool, project_id)
    engine_type = ocr_config.get('engine_type', 'pdfminer')

    doc_id = uuid.uuid4()
    safe_name = f'{doc_id}_{filename}'
    pdf_path = pdfs_dir / safe_name
    pdf_path.write_bytes(file_content)

    doc_record = await document_repo.create(
        pool,
        project_id=project_id,
        filename=filename,
        pdf_path=str(pdf_path),
        status='processing',
    )
    document_id = doc_record['id']

    try:
        pdf_doc = pdfium.PdfDocument(str(pdf_path))
        total_pages = len(pdf_doc)

        use_pdfminer = engine_type in ('pdfminer', 'pymupdf')
        page_info_list: list[dict] = []

        for page_no in range(total_pages):
            page = pdf_doc[page_no]
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()

            image_filename = f'{document_id}_p{page_no + 1}.png'
            image_path = images_dir / image_filename
            pil_image.save(str(image_path))

            width, height = pil_image.size

            # pdfminer fallback: synchronous extraction
            extracted = None
            if use_pdfminer:
                extracted = extraction_service.extract_page_elements(
                    pdf_path,
                    page_no=page_no,
                    scale=2.0,
                )

            page_record = await page_repo.create(
                pool,
                document_id=document_id,
                page_no=page_no + 1,
                width=width,
                height=height,
                image_path=str(image_path),
                auto_extracted_data=extracted,
            )

            # Collect page info for async extraction
            if not use_pdfminer:
                page_info_list.append(
                    {
                        'page_id': str(page_record['id']),
                        'page_idx': page_no,
                        'width': width,
                        'height': height,
                        'image_path': str(image_path),
                    }
                )

        pdf_doc.close()

        # Dispatch based on extraction provider
        if use_pdfminer:
            await document_repo.update_status(
                pool,
                document_id=document_id,
                status='ready',
                total_pages=total_pages,
            )
            return {
                'id': document_id,
                'filename': filename,
                'total_pages': total_pages,
                'status': 'ready',
            }

        # Async extraction via background task
        await document_repo.update_status(
            pool,
            document_id=document_id,
            status='extracting',
            total_pages=total_pages,
        )

        _task = asyncio.create_task(
            _run_ocr_extraction_background(
                pool,
                document_id,
                page_info_list,
                ocr_config,
            )
        )
        _task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)

        return {
            'id': document_id,
            'filename': filename,
            'total_pages': total_pages,
            'status': 'extracting',
        }

    except Exception:
        logger.exception('Failed to process PDF: %s', filename)
        await document_repo.update_status(pool, document_id=document_id, status='error')
        raise


async def _resolve_ocr_config(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Resolve OCR configuration from project settings.

    Args:
        pool: Database connection pool.
        project_id: Project UUID.

    Returns:
        OCR config dict with at least an 'engine_type' key.
    """
    config = await project_repo.get_ocr_config(pool, project_id)
    if config and config.get('engine_type'):
        return config
    return {'engine_type': 'pdfminer'}


async def _run_ocr_extraction_background(
    pool: asyncpg.Pool,
    document_id: uuid.UUID,
    page_info_list: list[dict],
    ocr_config: dict[str, Any],
) -> None:
    """Run OCR extraction as a background asyncio task.

    Builds an OCR engine and extracts each page in a thread pool,
    then updates the database with results via asyncpg.

    Args:
        pool: Database connection pool.
        document_id: Document UUID.
        page_info_list: List of page info dicts with keys:
            page_id, page_idx, width, height, image_path.
        ocr_config: OCR provider configuration dict.
    """
    engine_type = ocr_config.get('engine_type', 'unknown')
    logger.info(
        'Starting OCR extraction for document %s (%d pages, engine=%s)',
        document_id,
        len(page_info_list),
        engine_type,
    )

    try:
        engine = build_engine(ocr_config)

        for page in page_info_list:
            page_id = page['page_id']
            page_idx = page['page_idx']

            logger.info('Extracting page %s (idx=%d) with %s', page_id, page_idx, engine_type)

            extracted = await asyncio.to_thread(
                engine.extract_page,
                Path(page['image_path']),
                page['width'],
                page['height'],
            )

            await page_repo.update_auto_extracted_data(
                pool,
                uuid.UUID(page_id),
                extracted,
            )

            logger.info(
                'Updated page %s (idx=%d) with %d elements',
                page_id,
                page_idx,
                len(extracted.get('layout_dets', [])),
            )

        await document_repo.update_status(pool, document_id=document_id, status='ready')
        logger.info('OCR extraction completed for document %s', document_id)

    except Exception:
        logger.exception('OCR extraction failed for document %s', document_id)
        await document_repo.update_status(
            pool,
            document_id=document_id,
            status='extraction_failed',
        )


async def delete_with_files(
    pool: asyncpg.Pool,
    document_id: uuid.UUID,
) -> bool:
    """Delete a document and its associated storage files.

    Args:
        pool: Database connection pool.
        document_id: Document UUID.

    Returns:
        bool: True if document was deleted.
    """
    doc = await document_repo.get_by_id(pool, document_id)
    if doc is None:
        return False

    # Collect file paths before DB delete
    pdf_path = Path(doc['pdf_path']) if doc['pdf_path'] else None
    pages = await page_repo.list_by_document(pool, document_id)
    image_paths = [Path(p['image_path']) for p in pages if p.get('image_path')]

    # DB delete (cascades to pages, task_history)
    deleted = await document_repo.delete(pool, document_id)

    # Clean up storage files
    if deleted:
        if pdf_path and pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
        for img in image_paths:
            if img.exists():
                img.unlink(missing_ok=True)

    return deleted
