import asyncio
import json
import logging
import re
from datetime import datetime
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm import get_llm_client
from app.models.cv import CV
from app.models.job import Job
from app.models.user import User
from app.models.user_job_profile import UserJobProfile
from app.services.search.adzuna import AdzunaService
from app.services.search.arbeitnow import ArbeitnowService
from app.services.search.france_travail import FranceTravailService
from app.services.search.jobspy_scraper import JobSpyScraper
from app.services.search.normalizer import JobNormalizer
from app.services.search.remotive import RemotiveService

logger = logging.getLogger(__name__)


class SearchAgent:

    def __init__(self):
        self.client = get_llm_client()
        self.france_travail = FranceTravailService()
        self.adzuna = AdzunaService()
        self.arbeitnow = ArbeitnowService()
        self.remotive = RemotiveService()
        self.jobspy = JobSpyScraper()
        self.normalizer = JobNormalizer()

    def analyze_profile(self, profile: dict) -> dict:
        try:
            prompt = (
                "You are a senior HR expert. Generate the best search keywords for this candidate profile. "
                "Return ONLY a JSON object:\n"
                '{"primary_keywords": "string", "secondary_keywords": ["..."], "synonyms": ["..."]}\n\n'
                f"Profile: {json.dumps(profile, ensure_ascii=False)}"
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
            logger.warning(f"analyze_profile error: {e}")
            return {"primary_keywords": profile.get("target_role", "")}

    async def search_all(self, keywords: str, location: str) -> list[dict]:
        tasks = [
            self.france_travail.search(keywords, location),
            self.adzuna.search(keywords, location),
            self.arbeitnow.search(keywords),
            self.remotive.search(keywords),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        jobs = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Search source error: {r}")
                continue
            jobs.extend(r)

        try:
            loop = asyncio.get_event_loop()
            jobspy_results = await loop.run_in_executor(
                None, lambda: self.jobspy.scrape(keywords, location)
            )
            jobs.extend(jobspy_results)
        except Exception as e:
            logger.warning(f"JobSpy error: {e}")

        jobs = self.normalizer.deduplicate(jobs)
        logger.info(f"search_all total after dedup: {len(jobs)}")
        return jobs

    def _pre_filter(self, job: dict, profile_dict: dict) -> bool:
        target_role = profile_dict.get("target_role") or ""
        skills = profile_dict.get("skills") or []
        target_words = set(
            w.lower() for w in (target_role + " " + " ".join(skills)).split()
            if len(w) > 2
        )
        if not target_words:
            return True
        job_text = " ".join([
            job.get("title", "") or "",
            " ".join(job.get("skills_required", []) or []),
            (job.get("description", "") or "")[:500],
        ]).lower()
        return any(word in job_text for word in target_words)

    def score_jobs_batch(self, cv_structured: dict, jobs: list[dict]) -> list[dict]:
        cv_summary = {
            "years_experience": cv_structured.get("years_experience", 0),
            "skills": cv_structured.get("skills", [])[:15],
            "current_title": (cv_structured.get("experiences") or [{}])[0].get("title", ""),
        }
        jobs_list = [
            {
                "index": i,
                "title": job.get("title"),
                "skills_required": (job.get("skills_required") or [])[:10],
                "description": (job.get("description") or "")[:300],
            }
            for i, job in enumerate(jobs)
        ]
        prompt = (
            "You are a senior HR expert. Score each CV/job match below.\n"
            "Return ONLY a JSON array with one object per job:\n"
            '[{"index":0,"score":0-100,"matching_skills":[],"missing_skills":[],'
            '"verdict":"strong_match|good_match|weak_match|no_match","summary":"string"}, ...]\n\n'
            f"CV: {json.dumps(cv_summary, ensure_ascii=False)}\n"
            f"Jobs: {json.dumps(jobs_list, ensure_ascii=False)}"
        )
        resp = self.client.chat.completions.create(
            model=settings.LLM_MODEL_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
        results_by_index = {r["index"]: r for r in json.loads(raw)}
        return [
            results_by_index.get(i, {
                "score": 0, "matching_skills": [], "missing_skills": [],
                "verdict": "no_match", "summary": "",
            })
            for i in range(len(jobs))
        ]

    def score_job(self, cv_structured: dict, job: dict) -> dict:
        try:
            cv_summary = {
                "years_experience": cv_structured.get("years_experience", 0),
                "skills": cv_structured.get("skills", [])[:15],
                "current_title": (cv_structured.get("experiences") or [{}])[0].get("title", ""),
            }
            job_summary = {
                "title": job.get("title"),
                "skills_required": (job.get("skills_required") or [])[:10],
                "description": (job.get("description") or "")[:400],
            }
            prompt = (
                "Score this CV/job match. "
                "Return ONLY a JSON object:\n"
                '{"score": 0-100, "matching_skills": [], "missing_skills": [], '
                '"verdict": "strong_match|good_match|weak_match|no_match", "summary": "string"}\n\n'
                f"CV: {json.dumps(cv_summary, ensure_ascii=False)}\n"
                f"Job: {json.dumps(job_summary, ensure_ascii=False)}"
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
            logger.warning(f"score_job error: {e}")
            return {"score": 0, "matching_skills": [], "missing_skills": [], "verdict": "no_match", "summary": ""}

    def run(self, user_id: uuid.UUID, db: Session) -> dict:
        # if isinstance(user_id, str):
        #     user_id = uuid.UUID(user_id)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            logger.warning(f"User {user_id} not found or inactive")
            return {"new_jobs": 0, "total_searched": 0}

        cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.version.desc()).first()
        if not cv:
            logger.warning(f"No CV for user {user_id}")
            return {"new_jobs": 0, "total_searched": 0}

        profile = db.query(UserJobProfile).filter(UserJobProfile.user_id == user_id).first()
        if not profile:
            logger.warning(f"No job profile for user {user_id}")
            return {"new_jobs": 0, "total_searched": 0}

        profile_dict = {
            "target_role": profile.target_role,
            "location": profile.location,
            "skills": profile.skills,
            "years_experience": profile.years_experience,
        }

        keywords_data = self.analyze_profile(profile_dict)
        primary_keywords = keywords_data.get("primary_keywords", profile.target_role)
        secondary_keywords = keywords_data.get("secondary_keywords", [])

        loop = asyncio.new_event_loop()
        try:
            all_jobs = loop.run_until_complete(self.search_all(primary_keywords, profile.location))
            for kw in secondary_keywords[:2]:
                extra = loop.run_until_complete(self.search_all(kw, profile.location))
                all_jobs.extend(extra)
        finally:
            loop.close()

        jobs = self.normalizer.deduplicate(all_jobs)
        logger.info(f"Total jobs after multi-keyword search + dedup: {len(jobs)}")

        cv_structured = cv.data or {}
        new_jobs_count = 0

        BATCH_SIZE = 20
        logger.info(f"Starting pre-filter on {len(jobs)} jobs, profile: target_role={profile_dict.get('target_role')!r}, skills={profile_dict.get('skills')}")
        try:
            filtered = [j for j in jobs if self._pre_filter(j, profile_dict)]
        except Exception as e:
            logger.error(f"Pre-filter crashed: {e}", exc_info=True)
            filtered = jobs
        logger.info(f"Pre-filter: {len(jobs)} → {len(filtered)} jobs")

        scored_pairs: list[tuple[dict, dict]] = []
        for i in range(0, len(filtered), BATCH_SIZE):
            batch = filtered[i:i + BATCH_SIZE]
            try:
                score_results = self.score_jobs_batch(cv_structured, batch)
            except Exception as e:
                logger.warning(f"Batch scoring error, falling back to individual scoring: {e}")
                score_results = [self.score_job(cv_structured, j) for j in batch]
            scored_pairs.extend(zip(batch, score_results))

        above_threshold = sum(1 for _, s in scored_pairs if s.get("score", 0) >= 30)
        logger.info(f"Scoring done: {len(scored_pairs)} jobs scored, {above_threshold} above threshold (>=30)")

        for job_data, score_result in scored_pairs:
            score = score_result.get("score", 0)

            logger.info(f"Job '{job_data.get('title')}' score: {score}")
            print(f"Job '{job_data.get('title')}' score: {score}")
            
            if score < 60:
                continue

            external_id = job_data.get("external_id")
            if external_id is not None:
                existing = db.query(Job).filter(
                    Job.user_id == user_id,
                    Job.external_id == external_id,
                    Job.source == job_data.get("source"),
                ).first()
            else:
                url = job_data.get("url")
                existing = db.query(Job).filter(
                    Job.user_id == user_id,
                    Job.url == url,
                ).first() if url else None

            if existing:
                continue

            published_at = None
            if job_data.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(str(job_data["published_at"]))
                except Exception:
                    pass

            new_job = Job(
                user_id=user_id,
                external_id=job_data.get("external_id"),
                source=job_data.get("source"),
                title=job_data.get("title"),
                company=job_data.get("company"),
                location=job_data.get("location"),
                remote=job_data.get("remote"),
                contract=job_data.get("contract"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                description=job_data.get("description"),
                skills_required=job_data.get("skills_required", []),
                url=job_data.get("url"),
                apply_type=job_data.get("apply_type", "external"),
                match_score=score,
                match_details=score_result,
                published_at=published_at,
            )
            db.add(new_job)
            new_jobs_count += 1

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            logger.warning(f"Commit failed due to duplicate constraint, rolling back")
        logger.info(f"User {user_id}: {new_jobs_count} new jobs saved from {len(jobs)} searched")
        return {"new_jobs": new_jobs_count, "total_searched": len(jobs)}