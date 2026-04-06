import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.ats import ATSAnalysisOut
from app.schemas.job import JobListOut, JobOut, JobStatsOut
from app.services.ats_service import run_ats_analysis
from app.services.ats_apply_service import apply_ats_and_generate_pdf
from app.tasks.jobs_tasks import refresh_jobs_for_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/", response_model=JobListOut)
def list_jobs(
    min_score: Optional[float] = None,
    source: Optional[str] = None,
    contract: Optional[str] = None,
    remote: Optional[str] = None,
    is_saved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)
    if source:
        query = query.filter(Job.source == source)
    if contract:
        query = query.filter(Job.contract == contract)
    if remote:
        query = query.filter(Job.remote == remote)
    if is_saved is not None:
        query = query.filter(Job.is_saved == is_saved)

    total = query.count()
    jobs = query.order_by(Job.match_score.desc()).offset(skip).limit(limit).all()

    return JobListOut(total=total, jobs=jobs)


@router.get("/stats", response_model=JobStatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = db.query(Job).filter(Job.user_id == current_user.id)

    total = base.count()
    seen = base.filter(Job.is_seen == True).count()
    saved = base.filter(Job.is_saved == True).count()
    avg_score = db.query(func.avg(Job.match_score)).filter(Job.user_id == current_user.id).scalar() or 0.0

    by_source_rows = (
        db.query(Job.source, func.count(Job.id))
        .filter(Job.user_id == current_user.id)
        .group_by(Job.source)
        .all()
    )
    by_contract_rows = (
        db.query(Job.contract, func.count(Job.id))
        .filter(Job.user_id == current_user.id)
        .group_by(Job.contract)
        .all()
    )

    return JobStatsOut(
        total=total,
        seen=seen,
        saved=saved,
        avg_score=round(float(avg_score), 1),
        by_source={source: count for source, count in by_source_rows if source},
        by_contract={contract: count for contract, count in by_contract_rows if contract},
    )


@router.get("/{job_id}/ats", response_model=ATSAnalysisOut)
def analyze_ats(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return run_ats_analysis(job_id, current_user, db)


@router.post("/{job_id}/ats/apply")
def apply_ats(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pdf_bytes = apply_ats_and_generate_pdf(job_id, current_user, db)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cv_ats_{job_id}.pdf"},
    )


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.is_seen = True
    db.commit()
    db.refresh(job)
    return job


@router.patch("/{job_id}/save")
def toggle_save(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.is_saved = not job.is_saved
    db.commit()
    return {"is_saved": job.is_saved}


@router.post("/refresh")
def trigger_refresh(
    current_user: User = Depends(get_current_user),
):
    refresh_jobs_for_user.delay(str(current_user.id))
    return {"message": "Job refresh started"}