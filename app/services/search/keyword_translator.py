import logging
import redis
from app.core.config import settings
from app.core.llm import get_llm_client

logger = logging.getLogger(__name__)

_TTL = 30 * 24 * 3600  # 30 days


def _redis() -> redis.Redis:
    return redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


def translate_for_france_travail(keyword: str) -> str:
    """
    Translate a job search keyword to French for the France Travail API.
    - Redis cache (TTL 30 days): ~1ms on hit
    - LLM fast model on miss: ~300-500ms, then cached forever
    - Silent fallback to original keyword if both fail (no crash)
    """
    if not keyword:
        return keyword

    cache_key = f"ft_kw:{keyword.lower().strip()}"

    # 1. Redis cache lookup
    try:
        cached = _redis().get(cache_key)
        if cached:
            logger.debug(f"Keyword translation cache hit: '{keyword}' → '{cached}'")
            return cached
    except Exception as e:
        logger.warning(f"Redis unavailable for keyword translation: {e!r}")

    # 2. LLM translation
    try:
        client = get_llm_client()
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL_FAST,
            messages=[{
                "role": "user",
                "content": (
                    "You are a job search expert. Translate the following job search keyword to French.\n"
                    "Rules:\n"
                    "- Return ONLY the translated keyword, no explanation\n"
                    "- If already in French, return as-is\n"
                    "- Prefer the most common French job title used in French job postings\n\n"
                    f"Keyword: {keyword}"
                ),
            }],
            temperature=0,
        )
        translated = resp.choices[0].message.content.strip()
        logger.info(f"Keyword translated: '{keyword}' → '{translated}'")

        # 3. Store in Redis
        try:
            _redis().set(cache_key, translated, ex=_TTL)
        except Exception as e:
            logger.warning(f"Failed to cache keyword translation: {e!r}")

        return translated

    except Exception as e:
        logger.warning(f"Keyword translation failed for '{keyword}': {e!r} — using original")
        return keyword