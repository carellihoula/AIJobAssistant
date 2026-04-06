import json
import logging
import re

from fastapi import HTTPException

from app.core.config import settings
from app.core.llm import get_llm_client
from app.utils.prompts import generate_ats_prompt

logger = logging.getLogger(__name__)


class ATSAnalyzer:

    def __init__(self):
        self.client = get_llm_client()

    def analyze(self, cv: dict, job: dict) -> dict:
        prompt = generate_ats_prompt(cv, job)
        try:
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL_SMART,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"ATSAnalyzer JSON parse error: {e}")
            raise HTTPException(status_code=502, detail="ATS analysis failed: invalid LLM response")
        except Exception as e:
            logger.error(f"ATSAnalyzer error: {e}")
            raise HTTPException(status_code=502, detail="ATS analysis failed")