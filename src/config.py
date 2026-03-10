"""Central configuration loaded from .env via pydantic-settings."""

from pathlib import Path
import logging

from openai import OpenAI
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    # API Keys
    openai_api_key: str
    google_api_key: str

    # LLM Config
    llm_model: str = "gpt-4o"
    image_model: str = "gemini-3.1-flash-image-preview"
    image_aspect_ratio: str = "16:9"
    image_resolution: str = "2K"

    # Pipeline Config
    max_refinement_rounds: int = Field(default=3, ge=1, le=10)
    num_references: int = Field(default=5, ge=1, le=20)

    # Paths (resolved to absolute via validator)
    output_dir: Path = Path("output")
    references_dir: Path = Path("references")
    style_guide_path: Path = Path("config/style_guide.md")
    prompts_path: Path = Path("config/prompts.yaml")

    # Logging
    log_level: str = "INFO"

    @field_validator(
        "output_dir", "references_dir", "style_guide_path", "prompts_path",
        mode="before",
    )
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Resolve relative paths against project root."""
        path = Path(v)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


IMAGE_MODELS: dict[str, dict] = {
    "gemini-3.1-flash-image-preview": {"label": "Nano Banana 2 \U0001f34c"},
    "gemini-2.5-flash-image":         {"label": "Nano Banana \U0001f34c"},
}

# Module-level singleton
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# OpenAI client singleton
client = OpenAI(api_key=settings.openai_api_key)

# Google GenAI client singleton (lazy-initialised)
_google_client = None


def get_google_client():
    global _google_client
    if _google_client is None:
        from google import genai
        _google_client = genai.Client(api_key=settings.google_api_key)
    return _google_client
