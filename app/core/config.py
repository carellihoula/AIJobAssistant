"""
Centralized application configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings"""
    
    # security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # App
    APP_NAME: str = os.getenv("APP_NAME", "AI Job Assistant")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Keys (legacy)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

    # Universal LLM
    # LLM_PROVIDER: "openai" (default, covers DeepSeek/Groq/Mistral/Ollama) | "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_FAST: str = os.getenv("LLM_MODEL_FAST", "gpt-4o-mini")
    LLM_MODEL_SMART: str = os.getenv("LLM_MODEL_SMART", "gpt-4o")

    # Job search APIs
    FRANCE_TRAVAIL_CLIENT_ID: str = os.getenv("FRANCE_TRAVAIL_CLIENT_ID", "")
    FRANCE_TRAVAIL_CLIENT_SECRET: str = os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET", "")
    ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
    ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "")

    # Celery / Redis
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")

    # SMTP settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # FRONTEND settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")

# Instance
settings = Settings()