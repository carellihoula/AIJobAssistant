import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/fr/search"


class AdzunaService:

    async def search(self, keywords: str, location: str, pages: int = 3) -> list[dict]:
        try:
            jobs = []
            async with httpx.AsyncClient() as client:
                for page in range(1, pages + 1):
                    params = {
                        "app_id": settings.ADZUNA_APP_ID,
                        "app_key": settings.ADZUNA_APP_KEY,
                        "what": keywords,
                        "where": location,
                        "results_per_page": 20,
                        "content-type": "application/json",
                    }
                    resp = await client.get(
                        f"{BASE_URL}/{page}",
                        params=params,
                        timeout=15,
                    )
                    if resp.status_code != 200:
                        break
                    results = resp.json().get("results", [])
                    if not results:
                        break
                    jobs.extend([self._normalize(j) for j in results])
            logger.info(f"Adzuna: {len(jobs)} jobs found")
            return jobs
        except Exception as e:
            logger.error(f"Adzuna search error: {e}")
            return []

    def _normalize(self, job: dict) -> dict:
        return {
            "external_id": str(job.get("id")),
            "source": "adzuna",
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "remote": None,
            "contract": job.get("contract_type"),
            "salary_min": int(job["salary_min"]) if job.get("salary_min") else None,
            "salary_max": int(job["salary_max"]) if job.get("salary_max") else None,
            "description": job.get("description"),
            "skills_required": [],
            "url": job.get("redirect_url"),
            "apply_type": "external",
            "published_at": job.get("created"),
        }
