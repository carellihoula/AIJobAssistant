import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai_engine.scoring.ats_analyzer import ATSAnalyzer
from app.models.cv import CV
from app.models.job import Job


def run_ats_analysis(job_id: uuid.UUID, current_user, db: Session) -> dict:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.version.desc())
        .first()
    )
    if not cv:
        raise HTTPException(status_code=404, detail="No CV found. Please upload your CV first.")

    job_dict = {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "skills_required": job.skills_required or [],
    }

    analyzer = ATSAnalyzer()
    return analyzer.analyze(cv.data or {}, job_dict)