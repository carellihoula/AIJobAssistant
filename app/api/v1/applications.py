import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.document_agent import DocumentAgent
from app.agents.apply_agent import ApplyAgent
from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.cv import CV
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationStatusUpdate

logger = logging.getLogger(__name__)

ALLOWED_STATUS_TRANSITIONS = {"submitted", "interview", "rejected", "offer"}

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationOut)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == payload.job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cv = db.query(CV).filter(CV.user_id == current_user.id).order_by(CV.version.desc()).first()
    if not cv:
        raise HTTPException(status_code=404, detail="No CV found. Please upload your CV first.")

    cv_structured = cv.data or {}

    doc_agent = DocumentAgent()
    documents = doc_agent.run(cv_structured, job.__dict__)

    user_dict = {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": cv_structured.get("phone"),
        "linkedin": None,
    }

    apply_agent = ApplyAgent()
    package = apply_agent.run(job.__dict__, cv_structured, documents, user_dict)

    application = Application(
        user_id=current_user.id,
        job_id=job.id,
        tailored_cv=documents.get("tailored_cv"),
        cover_letter=documents.get("cover_letter"),
        apply_type=package.get("apply_type", "external"),
        status="ready",
        form_data=package.get("prefill_data") or package.get("subject") and {
            "subject": package.get("subject"),
            "body": package.get("body"),
            "recipient": package.get("recipient"),
        },
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=list[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}/status", response_model=ApplicationOut)
def update_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in ALLOWED_STATUS_TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed: {', '.join(ALLOWED_STATUS_TRANSITIONS)}",
        )

    app = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id,
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = payload.status
    if payload.status == "submitted":
        app.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(app)
    return app