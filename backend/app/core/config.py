from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InsightPilot API"
    environment: str = "development"
    log_level: str = "INFO"

    # Comma-separated list, e.g. "http://localhost:3000,https://myapp.vercel.app"
    allowed_origins: str = "http://localhost:3000"

    max_upload_mb: int = 50
    # Apply safe fixes (removing exact duplicate rows) right after upload; each one can be undone.
    auto_clean: bool = True
    storage_dir: Path = Path("sessions")
    # Demo datasets shown on the upload page (the repo's samples/ folder by default).
    samples_dir: Path = Path(__file__).resolve().parents[3] / "samples"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
