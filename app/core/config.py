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
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # App
    APP_NAME: str = os.getenv("APP_NAME", "AI Job Assistant")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

# Instance unique
settings = Settings()