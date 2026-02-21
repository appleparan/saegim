"""Celery application configuration for async task processing."""

from celery import Celery

from saegim.api.settings import get_settings

settings = get_settings()

celery_app = Celery(
    'saegim',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['saegim.tasks.ocr_extraction_task'],
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    # OCR extraction is heavy; process one task at a time
    worker_prefetch_multiplier=1,
    worker_concurrency=1,
    # Result expiry: 24 hours
    result_expires=86400,
    # Task time limits
    task_soft_time_limit=1800,  # 30 minutes soft limit
    task_time_limit=3600,  # 1 hour hard limit
)
