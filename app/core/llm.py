import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm_client():
    """
    Returns a unified LLM client with a consistent chat.completions.create() interface.

    Providers:
      LLM_PROVIDER=openai    → OpenAI / DeepSeek / Groq / Mistral / Ollama (OpenAI-compatible)
      LLM_PROVIDER=anthropic → Anthropic Claude (native SDK, adapted to match OpenAI interface)
    """
    if settings.LLM_PROVIDER == "anthropic":
        return _AnthropicAdapter(api_key=settings.LLM_API_KEY)
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


# ---------------------------------------------------------------------------
# Anthropic adapter — exposes the same interface as the OpenAI client
# so all agents can call client.chat.completions.create() without changes
# ---------------------------------------------------------------------------

class _Message:
    def __init__(self, content: str):
        self.content = content


class _Choice:
    def __init__(self, content: str):
        self.message = _Message(content)


class _Response:
    def __init__(self, content: str):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, anthropic_client):
        self._client = anthropic_client

    def create(self, model: str, messages: list, temperature: float = 1.0, **_) -> _Response:
        system_msg = None
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_messages.append({"role": m["role"], "content": m["content"]})

        create_kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": user_messages,
            "temperature": min(float(temperature), 1.0),  # Anthropic caps at 1.0
        }
        if system_msg:
            create_kwargs["system"] = system_msg

        response = self._client.messages.create(**create_kwargs)
        return _Response(response.content[0].text)


class _Chat:
    def __init__(self, anthropic_client):
        self.completions = _Completions(anthropic_client)


class _AnthropicAdapter:
    def __init__(self, api_key: str):
        try:
            import anthropic as _anthropic  # type: ignore[import]
            self._client = _anthropic.Anthropic(api_key=api_key)
            self.chat = _Chat(self._client)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
