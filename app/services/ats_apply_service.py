import uuid
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai_engine.scoring.ats_analyzer import ATSAnalyzer
from app.agents.document_agent import DocumentAgent
from app.models.cv import CV
from app.models.job import Job
from app.services.document.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


def apply_ats_and_generate_pdf(job_id: uuid.UUID, current_user, db: Session) -> bytes:
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

    cv_data = cv.data or {}
    job_dict = {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "skills_required": job.skills_required or [],
    }

    # Step 1: ATS analysis to get missing keywords and suggestions
    analyzer = ATSAnalyzer()
    ats_result = analyzer.analyze(cv_data, job_dict)

    # Step 2: Adapt CV using ATS results as context
    # Only highlight skills the candidate ALREADY HAS — never add missing ones
    job_analysis = {
        "tone": "corporate",
        "key_requirements": ats_result.get("present_keywords", []),
        "must_have_keywords": ats_result.get("present_keywords", []),
        "ats_format_suggestions": ats_result.get("improvement_suggestions", []),
        "skills_to_highlight": ats_result.get("present_keywords", []),
        "RULE": "NEVER add skills, technologies or experiences not present in the original CV",
    }

    agent = DocumentAgent()
    tailored_cv = agent.adapt_cv(cv_data, job_dict, job_analysis)

    # Apply the ATS-optimized summary (already constrained to existing CV content)
    if ats_result.get("tailored_summary"):
        tailored_cv["summary"] = ats_result["tailored_summary"]

    # Step 3: Generate PDF
    try:
        pdf_bytes = PDFGenerator().generate_cv(tailored_cv)
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return pdf_bytes