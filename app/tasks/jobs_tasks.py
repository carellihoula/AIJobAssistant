import logging
import uuid
from app.celery_app import celery
from app.db.session import SessionLocal
import app.models
from app.models.cv import CV
from app.models.user import User
from app.models.user_job_profile import UserJobProfile

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=120)
def refresh_jobs_for_user(self, user_id: str):
    from app.agents.search_agent import SearchAgent
    db = SessionLocal()
    try:
        user_uuid = uuid.UUID(user_id)
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user or not user.is_active:
            logger.warning(f"User {user_id} not found or inactive")
            return
        cv = db.query(CV).filter(CV.user_id == user_uuid).first()
        if not cv:
            logger.warning(f"No CV for user {user_id}")
            return

        profile = db.query(UserJobProfile).filter(UserJobProfile.user_id == user_uuid).first()
        if not profile:
            logger.warning(f"No profile for user {user_id}")
            return
        agent = SearchAgent()
        result = agent.run(user_uuid, db)
        logger.info(f"refresh_jobs_for_user {user_uuid}: {result}")
        return result
    except Exception as exc:
        logger.error(f"refresh_jobs_for_user error for {user_uuid}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery.task
def refresh_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            refresh_jobs_for_user.delay(str(user.id))
        logger.info(f"refresh_all_users: queued {len(users)} users")
    finally:
        db.close()