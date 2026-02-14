import tempfile
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.cv import CV
from app.utils.ocr import extract_text_from_pdf, extract_text_from_image
from app.ai_engine.parser.cv_ai_enricher import enrich_cv_with_llm

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


async def process_uploaded_cv(file: UploadFile, user, db: Session):
    """
    Handle file validation, OCR, AI enrichment and DB storage.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        total_size = 0
        CHUNK_SIZE = 1024 * 1024

        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File too large")
            tmp.write(chunk)

        tmp.flush()

        if extension == ".pdf":
            raw_text = extract_text_from_pdf(tmp.name)
        else:
            raw_text = extract_text_from_image(tmp.name)

    # AI enrichment
    cv = enrich_cv_with_llm(raw_text, email=user.email)

    if not cv.is_cv:
        return cv

    # Compute next version
    last_cv = (
        db.query(CV)
        .filter(CV.user_id == user.id)
        .order_by(CV.version.desc())
        .first()
    )
    next_version = (last_cv.version + 1) if last_cv else 1

    db_cv = CV(
        user_id=user.id,
        version=next_version,
        source="ai",
        data=cv.data.model_dump()
    )

    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    return cv


def create_manual_cv(cv_schema, user, db: Session):
    """
    Save manually created CV.
    """

    if not any([
        cv_schema.full_name,
        cv_schema.email,
        cv_schema.phone,
        cv_schema.summary,
        cv_schema.skills,
        cv_schema.experiences,
        cv_schema.education,
    ]):
        raise HTTPException(status_code=400, detail="CV cannot be empty")

    last_cv = (
        db.query(CV)
        .filter(CV.user_id == user.id)
        .order_by(CV.version.desc())
        .first()
    )
    next_version = (last_cv.version + 1) if last_cv else 1

    db_cv = CV(
        user_id=user.id,
        version=next_version,
        source="manual",
        data=cv_schema.model_dump(),
    )

    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)

    return cv_schema
