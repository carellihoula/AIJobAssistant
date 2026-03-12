import logging
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://remotive.com/api/remote-jobs"


class RemotiveService:

    async def search(self, keywords: str) -> list[dict]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    BASE_URL,
                    params={"search": keywords, "limit": 50},
                    timeout=15,
                )
                resp.raise_for_status()
                jobs = resp.json().get("jobs", [])
                result = [self._normalize(j) for j in jobs]
                logger.info(f"Remotive: {len(result)} jobs found")
                return result
        except Exception as e:
            logger.error(f"Remotive search error: {e}")
            return []

    def _normalize(self, job: dict) -> dict:
        return {
            "external_id": str(job.get("id")),
            "source": "remotive",
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("candidate_required_location"),
            "remote": "remote",
            "contract": job.get("job_type"),
            "salary_min": None,
            "salary_max": None,
            "description": job.get("description"),
            "skills_required": job.get("tags", []),
            "url": job.get("url"),
            "apply_type": "external",
            "published_at": job.get("publication_date"),
        }