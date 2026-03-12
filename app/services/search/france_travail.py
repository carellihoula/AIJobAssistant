import logging
import httpx
from dotenv import load_dotenv
load_dotenv()
from app.core.config import settings
from app.services.search.keyword_translator import translate_for_france_travail

logger = logging.getLogger(__name__)

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


class FranceTravailService:

    async def _get_token(self) -> str:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    TOKEN_URL,
                    params={"realm": "/partenaire"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.FRANCE_TRAVAIL_CLIENT_ID,
                        "client_secret": settings.FRANCE_TRAVAIL_CLIENT_SECRET,
                        "scope": "api_offresdemploiv2 o2dsoffre",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10,
                )
                resp.raise_for_status()
                logger.info(f"Successfully obtained FranceTravail access token {resp.json()['access_token']}")
                return resp.json()["access_token"]
        except Exception as e:
            logger.error(f"FranceTravail token error: {e!r}")
            raise

    # France Travail API requires INSEE commune codes, not city names.
    # Common codes: Paris=75056, Lyon=69123, Marseille=13055, Bordeaux=33063,
    # Toulouse=31555, Nantes=44109, Lille=59350, Strasbourg=67482, Nice=06088
    COMMUNE_CODES: dict[str, str] = {
        "paris": "75110",
        "lyon": "69123",
        "marseille": "13055",
        "bordeaux": "33063",
        "toulouse": "31555",
        "nantes": "44109",
        "lille": "59350",
        "strasbourg": "67482",
        "nice": "06088",
        "rennes": "35238",
        "montpellier": "34172",
        "grenoble": "38185",
    }

    DEPARTMENT_CODES: dict[str, str] = {
    "paris": "75",
    "lyon": "69",
    "marseille": "13",
    "bordeaux": "33",
    "toulouse": "31",
    "nantes": "44",
    "lille": "59",
    "strasbourg": "67",
    "nice": "06",
    "rennes": "35",
    "montpellier": "34",
    "grenoble": "38",
}

    def _resolve_commune(self, location: str) -> str | None:
        """Convert a city name to an INSEE commune code, or return as-is if already numeric."""
        if not location:
            return None
        if location.isdigit():
            return location
        return self.COMMUNE_CODES.get(location.lower().strip())

    async def search(self, keywords: str, location: str, pages: int = 3) -> list[dict]:
        try:
            token = await self._get_token()
            commune_code = self._resolve_commune(location)
            keywords = translate_for_france_travail(keywords)
            jobs = []
            async with httpx.AsyncClient() as client:
                for page in range(pages):
                    params: dict = {
                        "motsCles": keywords,
                        "range": f"{page * 20}-{page * 20 + 19}",
                    }
                    if commune_code:
                        params["commune"] = commune_code
                    resp = await client.get(
                        SEARCH_URL,
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=15,
                    )
                    if resp.status_code not in (200, 206):
                        break
                    data = resp.json()
                    results = data.get("resultats", [])
                    if not results:
                        break
                    jobs.extend([self._normalize(j) for j in results])
            logger.info(f"FranceTravail: {len(jobs)} jobs found")
            return jobs
        except Exception as e:
            logger.error(f"FranceTravail search error: {e!r}")
            return []

    def _normalize(self, job: dict) -> dict:

        return {
            "external_id": job.get("id"),
            "source": "france_travail",
            "title": job.get("intitule"),
            "company": job.get("entreprise", {}).get("nom"),
            "location": job.get("lieuTravail", {}).get("libelle"),
            "remote": job.get("typeContratLibelle"),
            "contract": job.get("typeContrat"),
            "salary_min": None,
            "salary_max": None,
            "description": job.get("description"),
            "skills_required": [c.get("libelle") for c in job.get("competences", [])],
            "url": job.get("origineOffre", {}).get("urlOrigine"),
            "apply_type": "external",
            "published_at": job.get("dateCreation"),
        }
