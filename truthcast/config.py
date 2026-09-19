"""Runtime settings, read once from the environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="TRUTHCAST_", extra="ignore"
    )

    # --- Claude ---
    model: str = "claude-opus-5"
    effort: str = "high"
    # Claim extraction is bulk work over a long transcript; a cheaper model keeps
    # the cost sane without touching the part that decides what is true.
    extraction_model: str = "claude-sonnet-5"

    # --- Verification bar ---
    # A claim only reaches the digest if the verifier is at least this sure AND
    # the supporting evidence spans at least this many independent domains.
    min_confidence: float = 0.75
    min_independent_sources: int = 2
    max_claims: int = 25
    max_searches_per_claim: int = 6
    include_corrections: bool = True

    # --- Explanation ---
    target_reading_grade: float = 5.0
    max_simplify_passes: int = 2

    # --- Speech ---
    tts_provider: str = "browser"
    tts_voice: str | None = None

    # --- Storage ---
    data_dir: Path = Path("./data")

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "truthcast.sqlite3"

    def ensure_dirs(self) -> None:
        for path in (self.data_dir, self.media_dir, self.audio_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
