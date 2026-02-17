"""Central configuration loaded from .env via pydantic-settings."""

from enum import Enum
from pathlib import Path
import logging

from openai import OpenAI
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageSize(str, Enum):
    SQUARE = "1024x1024"
    PORTRAIT = "1024x1536"
    LANDSCAPE = "1536x1024"


class ImageQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    # API Keys
    openai_api_key: str
    google_api_key: str | None = None

    # LLM Config
    llm_model: str = "gpt-4o"
    image_model: str = "gpt-image-1"
    image_size: ImageSize = ImageSize.LANDSCAPE
    image_quality: ImageQuality = ImageQuality.HIGH

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
    "gpt-image-1":                {"label": "GPT Image 1 (OpenAI)",    "provider": "openai"},
    "dall-e-3":                   {"label": "DALL-E 3 (OpenAI)",       "provider": "openai"},
    "gemini-2.5-flash-image": {"label": "Gemini 2.5 Flash (Google)", "provider": "google"},
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

# Lazy Google GenAI client
_google_client = None


def get_google_client():
    global _google_client
    if _google_client is None:
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for Gemini models. Set it in .env."
            )
        from google import genai
        _google_client = genai.Client(api_key=settings.google_api_key)
    return _google_client
