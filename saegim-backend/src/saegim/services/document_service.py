"""Document service for PDF upload and image conversion."""

import logging
import uuid
from pathlib import Path

import asyncpg
import fitz

from saegim.api.settings import get_settings
from saegim.repositories import document_repo, page_repo
from saegim.services import extraction_service

logger = logging.getLogger(__name__)


async def upload_and_convert(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    filename: str,
    file_content: bytes,
    storage_path: str,
) -> dict:
    """Upload a PDF and convert each page to an image.

    Renders page images at 2x scale. Extraction behavior depends on
    EXTRACTION_BACKEND setting:
    - 'pymupdf': Synchronous extraction via PyMuPDF (fallback for CI)
    - 'mineru': Dispatches async Celery task for MinerU extraction

    Args:
        pool: Database connection pool.
        project_id: Parent project UUID.
        filename: Original PDF filename.
        file_content: Raw PDF bytes.
        storage_path: Base storage directory path.

    Returns:
        dict: Document info with id, filename, total_pages, status.
    """
    settings = get_settings()
    storage = Path(storage_path)
    pdfs_dir = storage / 'pdfs'
    images_dir = storage / 'images'
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

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
        pdf_doc = fitz.open(str(pdf_path))
        total_pages = len(pdf_doc)

        use_pymupdf = settings.extraction_backend == 'pymupdf'
        page_info_list: list[dict] = []

        for page_no in range(total_pages):
            page = pdf_doc[page_no]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)

            image_filename = f'{document_id}_p{page_no + 1}.png'
            image_path = images_dir / image_filename
            pix.save(str(image_path))

            # PyMuPDF fallback: synchronous extraction
            extracted = None
            if use_pymupdf:
                extracted = extraction_service.extract_page_elements(page, scale=2.0)

            page_record = await page_repo.create(
                pool,
                document_id=document_id,
                page_no=page_no + 1,
                width=pix.width,
                height=pix.height,
                image_path=str(image_path),
                auto_extracted_data=extracted,
            )

            # Collect page info for MinerU async extraction
            if not use_pymupdf:
                page_info_list.append(
                    {
                        'page_id': str(page_record['id']),
                        'page_idx': page_no,
                        'width': pix.width,
                        'height': pix.height,
                    }
                )

        pdf_doc.close()

        # Dispatch based on extraction backend
        if use_pymupdf:
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
        else:
            # MinerU async extraction via Celery
            await document_repo.update_status(
                pool,
                document_id=document_id,
                status='extracting',
                total_pages=total_pages,
            )
            _dispatch_mineru_extraction(
                document_id=document_id,
                pdf_path=pdf_path,
                page_info_list=page_info_list,
                settings=settings,
            )
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


def _dispatch_mineru_extraction(
    document_id: uuid.UUID,
    pdf_path: Path,
    page_info_list: list[dict],
    settings: object,
) -> None:
    """Dispatch MinerU extraction as a Celery task.

    Args:
        document_id: Document UUID.
        pdf_path: Path to the PDF file.
        page_info_list: List of page info dicts for the Celery task.
        settings: Application settings with mineru_language and mineru_backend.
    """
    from saegim.tasks.extraction_task import run_mineru_extraction

    run_mineru_extraction.delay(
        document_id=str(document_id),
        pdf_path=str(pdf_path),
        page_info=page_info_list,
        language=settings.mineru_language,
        backend=settings.mineru_backend,
    )
    logger.info(
        'Dispatched MinerU extraction task for document %s (%d pages)',
        document_id,
        len(page_info_list),
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
