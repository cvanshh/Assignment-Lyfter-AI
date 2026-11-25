import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ or repository root when running locally without Docker
_here = Path(__file__).resolve().parent
load_dotenv(_here.parent / ".env", override=False)
load_dotenv(_here.parent.parent / ".env", override=False)

def _bool(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes")

class Settings:
    def __init__(self) -> None:
        self.keys = [k.strip() for k in os.getenv("LLM_API_KEYS", "").split(",") if k.strip()]
        self.model = os.getenv("LLM_MODEL", "gemini/gemini-flash-latest")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        raw_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        )
        self.origins = [o.strip().rstrip("/") for o in raw_origins.split(",") if o.strip()]
        self.simulate = _bool(os.getenv("ENABLE_FAILURE_SIMULATION", "false"))
        self.cache_type = os.getenv("CACHE_TYPE", "local")  # local | disk
        self.cache_dir = os.getenv("CACHE_DIR", "/data/llm_cache")
        self.mock = _bool(os.getenv("LLM_MOCK", "false"))  # offline mode for tests/demos
        self.cooldown = int(os.getenv("KEY_COOLDOWN_SECONDS", "30"))
        self.default_system = os.getenv("DEFAULT_SYSTEM_PROMPT", "You are a helpful, concise assistant.")

settings = Settings()
