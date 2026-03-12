import json
import logging
import re
from app.core.llm import get_llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobNormalizer:

    def __init__(self):
        self.client = get_llm_client()
        self.model = settings.LLM_MODEL_FAST

    def enrich(self, job: dict) -> dict:
        if not job.get("skills_required") and job.get("description"):
            try:
                prompt = (
                    "Extract the required technical skills from this job description. "
                    "Return ONLY a JSON object: {\"skills\": [\"skill1\", \"skill2\"]}\n\n"
                    f"Description: {job['description'][:800]}"
                )
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                raw = resp.choices[0].message.content.strip()
                raw = re.sub(r"^```json|^```|```$", "", raw).strip()
                data = json.loads(raw)
                job["skills_required"] = data.get("skills", [])
            except Exception as e:
                logger.warning(f"Enrich skills error: {e}")
        return job

    def deduplicate(self, jobs: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for job in jobs:
            key = (
                (job.get("title") or "").lower().strip(),
                (job.get("company") or "").lower().strip(),
                (job.get("location") or "").lower().strip(),
            )
            if key not in seen:
                seen.add(key)
                unique.append(job)
        logger.info(f"Deduplicated: {len(jobs)} → {len(unique)} jobs")
        return unique