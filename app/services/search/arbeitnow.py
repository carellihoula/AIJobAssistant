import logging
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowService:

    async def search(self, keywords: str, pages: int = 3) -> list[dict]:
        try:
            jobs = []
            async with httpx.AsyncClient() as client:
                for page in range(1, pages + 1):
                    resp = await client.get(
                        BASE_URL,
                        params={"q": keywords, "page": page},
                        timeout=15,
                    )
                    if resp.status_code != 200:
                        break
                    results = resp.json().get("data", [])
                    if not results:
                        break
                    jobs.extend([self._normalize(j) for j in results])
            logger.info(f"Arbeitnow: {len(jobs)} jobs found")
            return jobs
        except Exception as e:
            logger.error(f"Arbeitnow search error: {e}")
            return []

    def _normalize(self, job: dict) -> dict:
        return {
            "external_id": job.get("slug"),
            "source": "arbeitnow",
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "remote": "remote" if job.get("remote") else None,
            "contract": None,
            "salary_min": None,
            "salary_max": None,
            "description": job.get("description"),
            "skills_required": job.get("tags", []),
            "url": job.get("url"),
            "apply_type": "external",
            "published_at": None,
        }