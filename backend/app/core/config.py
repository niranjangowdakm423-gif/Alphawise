from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Explicitly load .env file from backend directory or project root
_backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")
load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Alphawise Portfolio Optimizer"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "https://alphawise.vercel.app",
        "*"
    ]
    DEFAULT_RISK_FREE_RATE: float = 0.045
    MAX_ASSETS_LIMIT: int = 30
    DEFAULT_LOOKBACK_YEARS: int = 3
    CACHE_EXPIRY_SECONDS: int = 3600  # 1 hour market data cache

    # LLM / Groq Configuration Defaults
    GROQ_API_KEY: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "openai/gpt-oss-120b"

    @property
    def active_api_key(self) -> str:
        return os.getenv("GROQ_API_KEY", "") or os.getenv("LLM_API_KEY", "") or self.GROQ_API_KEY or self.LLM_API_KEY or ""

    @property
    def active_model(self) -> str:
        return os.getenv("LLM_MODEL", "") or self.LLM_MODEL or "openai/gpt-oss-120b"


    @property
    def active_base_url(self) -> str:
        return os.getenv("LLM_BASE_URL", "") or self.LLM_BASE_URL or "https://api.groq.com/openai/v1"

settings = Settings()

