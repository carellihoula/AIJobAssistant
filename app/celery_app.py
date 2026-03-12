from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery(
    "ai_job_assistant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.jobs_tasks"],
)

celery.conf.beat_schedule = {
    "refresh-all-users-every-6h": {
        "task": "app.tasks.jobs_tasks.refresh_all_users",
        "schedule": crontab(hour="*/6"),
    },
}

celery.conf.timezone = "UTC"