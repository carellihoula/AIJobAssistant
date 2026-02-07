"""
CV endpoints: upload or manual creation.
"""
import logging
import shutil
from pathlib import Path
import tempfile
from app.ai_engine.parser.cv_ai_enricher import enrich_cv_with_llm
from app.db.session import SessionLocal
from app.models.cv import CV
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.ocr import extract_text_from_pdf, extract_text_from_image
from app.ai_engine.parser.cv_parser import parse_cv_text
from app.schemas.cv import CVParseResponse, CVSchema
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/cvs",
    tags=["CVs"]
)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Authorized extensions
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@router.post("/upload", response_model=CVParseResponse,)
async def upload_cv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """
    Upload a CV file (PDF / JPG / PNG) from web app.
    Extract text and enrich via GPT-4.
    """
    # print("=== DEBUG START ===")
    # print(f"File object: {file}")
    # print(f"File.filename: {file.filename}")
    # print(f"File.content_type: {file.content_type}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
    extension = Path(file.filename).suffix.lower()
    logging.info(f"Uploading CV: {file.filename} ({extension})")

    if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Use: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        total_size = 0
        CHUNK_SIZE = 1024 * 1024  # 1 MB per read
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE // (1024*1024)} MB")
            tmp.write(chunk)

        tmp.flush()
        
        if file.filename.lower().endswith(".pdf"):
            raw_text = extract_text_from_pdf(tmp.name)
        else:
            raw_text = extract_text_from_image(tmp.name)

    # Enrich via GPT-4
    try:
        cv = enrich_cv_with_llm(raw_text, email=current_user.email)
        # logging.info(f"CV parsing result: {cv}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching CV: {str(e)}")

    # NOT A CV → return JSON directly
    if not cv.is_cv:
        # logging.info(f"CV parsing failed or not a CV. {cv}")
        return cv

    # Valid CV → save to database
    db = SessionLocal()
    db_cv = CV(
        user_id=current_user.id,
        version=1,
        source="ai",
        data=cv.data.model_dump()
    )
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    return cv

@router.post("/manual", response_model=CVSchema)
def create_cv_manually(
    cv: CVSchema,
    current_user=Depends(get_current_user),
):
    """
    Create a CV from manual user input and save it to database.
    """

    # Minimal validation: at least one meaningful field
    if not any([
        cv.full_name,
        cv.email,
        cv.phone,
        cv.summary,
        cv.skills,
        cv.experiences,
        cv.education,
    ]):
        raise HTTPException(
            status_code=400,
            detail="CV cannot be empty"
        )

    db = SessionLocal()

    # Compute next version
    last_cv = (
        db.query(CV)
        .filter(CV.user_id == current_user.id)
        .order_by(CV.version.desc())
        .first()
    )
    next_version = (last_cv.version + 1) if last_cv else 1

    db_cv = CV(
        user_id=current_user.id,
        version=next_version,
        source="manual",
        data=cv.model_dump(),
    )

    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    return cv

