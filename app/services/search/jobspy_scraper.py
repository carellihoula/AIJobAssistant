import logging
from typing import Any

logger = logging.getLogger(__name__)


class JobSpyScraper:

    def scrape(self, keywords: str, location: str, max_jobs: int = 50) -> list[dict]:
        try:
            from jobspy import scrape_jobs
            df = scrape_jobs(
                site_name=["indeed", "glassdoor", "linkedin", "google"],
                search_term=keywords,
                location=location,
                results_wanted=max_jobs,
                country_indeed="France",
            )
            if df is None or df.empty:
                return []
            jobs = [self._normalize(row) for _, row in df.iterrows()]
            logger.info(f"JobSpy: {len(jobs)} jobs found")
            return jobs
        except Exception as e:
            logger.error(f"JobSpy scrape error: {e}")
            return []

    def _normalize(self, row: Any) -> dict:
        def safe(val):
            return None if (val is None or (hasattr(val, "__class__") and val.__class__.__name__ == "float" and str(val) == "nan")) else val

        return {
            "external_id": safe(row.get("id")),
            "source": safe(row.get("site")) or "indeed",
            "title": safe(row.get("title")),
            "company": safe(row.get("company")),
            "location": safe(row.get("location")),
            "remote": "remote" if safe(row.get("is_remote")) else None,
            "contract": str(safe(row.get("job_type"))) if safe(row.get("job_type")) else None,
            "salary_min": int(row["min_amount"]) if safe(row.get("min_amount")) else None,
            "salary_max": int(row["max_amount"]) if safe(row.get("max_amount")) else None,
            "description": safe(row.get("description")),
            "skills_required": [],
            "url": safe(row.get("job_url")),
            "apply_type": "external",
            "published_at": safe(row.get("date_posted")),
        }