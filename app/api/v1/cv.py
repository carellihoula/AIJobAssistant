"""
CV endpoints: upload or manual creation.
"""
import logging
import shutil
from pathlib import Path
import tempfile
from app.ai_engine.parser.cv_ai_enricher import enrich_cv_with_llm
from app.db.session import get_db
from app.models.cv import CV
from app.services.cv_service import create_manual_cv, process_uploaded_cv
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.ocr import extract_text_from_pdf, extract_text_from_image
# from app.ai_engine.parser.cv_parser import parse_cv_text
from app.schemas.cv import CVParseResponse, CVSchema
from app.core.auth import get_current_user
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/cvs",
    tags=["CVs"]
)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=CVParseResponse,)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db),current_user=Depends(get_current_user)):
    """
    Upload a CV file (PDF / JPG / PNG) from web app.
    Extract text and enrich via GPT-4.
    """
    return await process_uploaded_cv(file, current_user, db)

@router.post("/manual", response_model=CVSchema)
def create_cv_manually(
    cv: CVSchema,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a CV from manual user input and save it to database.
    """
    return create_manual_cv(cv, current_user, db)

@router.get("/me/latest", response_model=CVSchema)
def get_my_latest_cv(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.version.desc())
        .first()
    )

    if not cv:
        raise HTTPException(status_code=404, detail="No CV found")

    return cv.data

@router.get("/me", response_model=list[CVSchema])
def list_my_cvs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cvs = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.version.desc())
        .all()
    )

    return [cv.data for cv in cvs]
