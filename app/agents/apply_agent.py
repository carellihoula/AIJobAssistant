import json
import logging
import re

from app.core.config import settings
from app.core.llm import get_llm_client

logger = logging.getLogger(__name__)

PLATFORM_PATTERNS = {
    "greenhouse": "greenhouse.io",
    "lever": "lever.co",
    "workday": "workday.com",
    "teamtailor": "teamtailor.com",
}


class ApplyAgent:

    def __init__(self):
        self.client = get_llm_client()

    def detect_apply_type(self, job: dict) -> str:
        url = (job.get("url") or "").lower()
        apply_type = (job.get("apply_type") or "").lower()

        if apply_type == "easy_apply":
            return "easy_apply"
        for platform, pattern in PLATFORM_PATTERNS.items():
            if pattern in url:
                return platform
        if "mailto:" in url or "@" in (job.get("description") or ""):
            return "email"
        return "external"

    def prepare_email_application(self, job: dict, documents: dict, user: dict) -> dict:
        try:
            prompt = (
                "Generate a professional job application email. "
                "Return ONLY a JSON object:\n"
                '{"subject": "string", "body": "string", "recipient": "email or null"}\n\n'
                f"Role: {job.get('title')} at {job.get('company')}\n"
                f"Cover letter: {documents.get('cover_letter', '')[:800]}"
            )
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL_FAST,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json|^```|```$", "", raw).strip()
            email_data = json.loads(raw)
        except Exception as e:
            logger.warning(f"prepare_email_application LLM error: {e}")
            email_data = {
                "subject": f"Application — {job.get('title')}",
                "body": documents.get("cover_letter", ""),
                "recipient": None,
            }

        return {
            **email_data,
            "cv_pdf": documents.get("cv_pdf"),
            "cover_letter_pdf": documents.get("cover_letter_pdf"),
        }

    def prepare_external_application(self, job: dict, documents: dict, user: dict) -> dict:
        prefill_data = {
            "first_name": (user.get("full_name") or "").split(" ")[0],
            "last_name": " ".join((user.get("full_name") or "").split(" ")[1:]),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "linkedin": user.get("linkedin"),
        }
        return {
            "apply_url": job.get("url"),
            "instructions": f"Go to the link to apply for {job.get('title')} at {job.get('company')}.",
            "cv_pdf": documents.get("cv_pdf"),
            "cover_letter_pdf": documents.get("cover_letter_pdf"),
            "prefill_data": prefill_data,
        }

    def run(self, job: dict, cv_structured: dict, documents: dict, user: dict) -> dict:
        apply_type = self.detect_apply_type(job)

        if apply_type == "email":
            package = self.prepare_email_application(job, documents, user)
        else:
            package = self.prepare_external_application(job, documents, user)

        return {
            **package,
            "status": "ready",
            "apply_type": apply_type,
        }