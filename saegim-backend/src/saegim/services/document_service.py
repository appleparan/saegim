"""Document service for PDF upload and image conversion."""

import logging
import uuid
from pathlib import Path

import asyncpg
import fitz

from saegim.repositories import document_repo, page_repo

logger = logging.getLogger(__name__)


async def upload_and_convert(
    pool: asyncpg.Pool,
    project_id: uuid.UUID,
    filename: str,
    file_content: bytes,
    storage_path: str,
) -> dict:
    """Upload a PDF and convert each page to an image.

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

        for page_no in range(total_pages):
            page = pdf_doc[page_no]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)

            image_filename = f'{document_id}_p{page_no + 1}.png'
            image_path = images_dir / image_filename
            pix.save(str(image_path))

            await page_repo.create(
                pool,
                document_id=document_id,
                page_no=page_no + 1,
                width=pix.width,
                height=pix.height,
                image_path=str(image_path),
            )

        pdf_doc.close()

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

    except Exception:
        logger.exception('Failed to process PDF: %s', filename)
        await document_repo.update_status(pool, document_id=document_id, status='error')
        raise


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
