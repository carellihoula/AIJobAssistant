import json
import logging
import re

from app.core.config import settings
from app.core.llm import get_llm_client
from app.services.document.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class DocumentAgent:

    def __init__(self):
        self.client = get_llm_client()
        self.pdf_generator = PDFGenerator()

    def analyze_job(self, job: dict) -> dict:
        try:
            prompt = (
                "Analyze this job offer. "
                "Return ONLY a JSON object:\n"
                '{"tone": "startup|corporate|agency", "key_requirements": [], '
                '"company_culture": "string", "must_have_keywords": []}\n\n'
                f"Job offer: {json.dumps(job, ensure_ascii=False)}"
            )
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL_FAST,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json|^```|```$", "", raw).strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"analyze_job error: {e}")
            return {}

    def adapt_cv(self, original_cv: dict, job: dict, job_analysis: dict) -> dict:
        try:
            prompt = (
                "You are a senior HR expert. Adapt this CV for the following job offer.\n"
                "ABSOLUTE RULES:\n"
                "- Never invent experiences, skills or degrees\n"
                "- Only reorder and rephrase what already exists\n"
                "- Use the exact keywords from the job offer where relevant\n"
                "- Put the most relevant experiences first\n"
                "- Adapt the summary to the target position\n"
                "Return ONLY the CV JSON with the same structure.\n\n"
                f"Original CV: {json.dumps(original_cv, ensure_ascii=False)}\n"
                f"Job: title={job.get('title')}, company={job.get('company')}\n"
                f"Description: {(job.get('description') or '')[:600]}\n"
                f"Analysis: {json.dumps(job_analysis, ensure_ascii=False)}"
            )
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL_SMART,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json|^```|```$", "", raw).strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"adapt_cv error: {e}")
            return original_cv

    def generate_cover_letter(self, cv: dict, job: dict, job_analysis: dict) -> str:
        try:
            tone = job_analysis.get("tone", "corporate")
            prompt = (
                "Write a compelling cover letter.\n"
                f"STYLE based on tone={tone}:\n"
                "- 3 paragraphs max\n"
                "- Start with your concrete added value, not with 'I am writing to apply...'\n"
                "- Paragraph 2: why this specific company\n"
                "- Paragraph 3: precise call-to-action\n"
                f"- Tone: {tone}\n"
                "Return only the written letter, no comments.\n\n"
                f"Candidate: {cv.get('full_name')}, {cv.get('summary', '')[:300]}\n"
                f"Skills: {', '.join(cv.get('skills', [])[:10])}\n"
                f"Target role: {job.get('title')} at {job.get('company')}\n"
                f"Job description: {(job.get('description') or '')[:500]}"
            )
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL_SMART,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"generate_cover_letter error: {e}")
            return ""

    def run(self, cv_structured: dict, job: dict) -> dict:
        job_analysis = self.analyze_job(job)
        tailored_cv = self.adapt_cv(cv_structured, job, job_analysis)
        cover_letter = self.generate_cover_letter(cv_structured, job, job_analysis)

        try:
            cv_pdf = self.pdf_generator.generate_cv(tailored_cv)
        except Exception as e:
            logger.error(f"CV PDF error: {e}")
            cv_pdf = b""

        try:
            cl_pdf = self.pdf_generator.generate_cover_letter(
                cover_letter,
                personal={
                    "full_name": cv_structured.get("full_name"),
                    "email": cv_structured.get("email"),
                    "phone": cv_structured.get("phone"),
                    "location": cv_structured.get("location"),
                },
            )
        except Exception as e:
            logger.error(f"Cover letter PDF error: {e}")
            cl_pdf = b""

        return {
            "tailored_cv": tailored_cv,
            "cover_letter": cover_letter,
            "cv_pdf": cv_pdf,
            "cover_letter_pdf": cl_pdf,
            "job_analysis": job_analysis,
        }