import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.user_job_profile import UserJobProfile
from app.schemas.profile import UserJobProfileCreate, UserJobProfileOut
from app.tasks.jobs_tasks import refresh_jobs_for_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/", response_model=UserJobProfileOut)
def upsert_profile(
    payload: UserJobProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserJobProfile).filter(UserJobProfile.user_id == current_user.id).first()

    if profile:
        profile.target_role = payload.target_role
        profile.location = payload.location
        profile.remote_preference = payload.remote_preference
        profile.contract_preference = payload.contract_preference
        profile.min_salary = payload.min_salary
        profile.skills = payload.skills
        profile.years_experience = payload.years_experience
        profile.updated_at = datetime.utcnow()
    else:
        profile = UserJobProfile(
            user_id=current_user.id,
            target_role=payload.target_role,
            location=payload.location,
            remote_preference=payload.remote_preference,
            contract_preference=payload.contract_preference,
            min_salary=payload.min_salary,
            skills=payload.skills,
            years_experience=payload.years_experience,
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    refresh_jobs_for_user.delay(str(current_user.id))

    return profile


@router.get("/", response_model=UserJobProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserJobProfile).filter(UserJobProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile