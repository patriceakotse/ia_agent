from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Agent Orchestrator"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./agent_orchestrator.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    
    # Default LLM Settings
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    
    # xAI (Grok) Settings
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_MODEL: str = "grok-4.3"
    
    # OpenHands
    OPENHANDS_URL: str = "http://localhost:3000"
    OPENHANDS_API_KEY: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()