"""Visualizer agent: generate an image from the styled description."""

import base64
import logging

from src.config import client, settings
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    """Load and cache the visualizer system prompt."""
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = get_prompt("visualizer_system")
    return _system_prompt


def generate_image(styled_description: str) -> bytes:
    """
    Generate an image using the configured image generation model.

    Prepends the visualizer system prompt to the styled description
    to set the role and quality expectations for the image model.
    Returns raw image bytes (PNG/WEBP/JPEG depending on config).
    """
    logger.info(
        "Generating image with model=%s, size=%s, quality=%s",
        settings.image_model,
        settings.image_size.value,
        settings.image_quality.value,
    )

    full_prompt = f"{_get_system_prompt()}\n\n{styled_description}"

    kwargs = dict(
        model=settings.image_model,
        prompt=full_prompt,
        size=settings.image_size.value,
        quality=settings.image_quality.value,
        n=1,
    )
    # gpt-image-1 returns base64 by default; DALL-E models need this explicitly
    if settings.image_model.startswith("dall-e"):
        kwargs["response_format"] = "b64_json"

    response = client.images.generate(**kwargs)

    image_base64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    logger.info("Generated image: %d bytes", len(image_bytes))
    return image_bytes
