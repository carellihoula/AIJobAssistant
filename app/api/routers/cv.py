"""
CV endpoints: upload or manual creation.
"""
import shutil
from pathlib import Path
import tempfile
from app.ai_engine.parser.cv_ai_enricher import enrich_cv_with_llm
from app.db.session import SessionLocal
from app.models.cv import CV
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.ocr import extract_text_from_pdf, extract_text_from_image
from app.ai_engine.parser.cv_parser import parse_cv_text
from app.schemas.cv import CVSchema
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

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """
    Upload a CV file (PDF / JPG / PNG) from web app.
    Extract text and enrich via GPT-4.
    """
    if not file.filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching CV: {str(e)}")
    
     # Sauvegarde DB
    db = SessionLocal()
    db_cv = CV(
        user_id=current_user.id,
        version=1,
        source="ai",
        data=cv.model_dump()
    )
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    return db_cv.data


@router.post("/cv/manual", response_model=CVSchema)
def create_cv_manually(cv: CVSchema):
    """
    Create CV from manual user input.
    """
    return cv
