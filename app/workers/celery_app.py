"""
Celery application configuration.

Configures Celery for background task processing.
"""

from celery import Celery
from celery.schedules import crontab
from config.settings import settings

# Create Celery application
celery_app = Celery(
    "stock_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "update-stock-prices": {
        "task": "app.workers.tasks.update_all_stock_prices",
        "schedule": settings.PRICE_UPDATE_INTERVAL_SECONDS,
    },
    "check-alerts": {
        "task": "app.workers.tasks.check_all_alerts",
        "schedule": settings.ALERT_CHECK_INTERVAL_SECONDS,
    },
    "cleanup-old-data": {
        "task": "app.workers.tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
