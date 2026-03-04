"""Visualizer agent: generate an image from the styled description via Gemini."""

import logging

from google.genai import types

from src.config import get_google_client, settings
from src.utils.image_utils import normalize_to_png
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    """Load and cache the visualizer system prompt."""
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = get_prompt("visualizer_system")
    return _system_prompt


def generate_image(styled_description: str, image_model: str | None = None) -> bytes:
    """Generate an image using the Gemini API.

    Always returns PNG bytes.
    """
    model = image_model or settings.image_model

    logger.info(
        "Generating image with model=%s, aspect_ratio=%s, resolution=%s",
        model,
        settings.image_aspect_ratio,
        settings.image_resolution,
    )

    full_prompt = f"{_get_system_prompt()}\n\n{styled_description}"

    client = get_google_client()
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=settings.image_aspect_ratio,
                image_size=settings.image_resolution,
            ),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = normalize_to_png(part.inline_data.data)
            logger.info("Generated image: %d bytes", len(image_bytes))
            return image_bytes

    raise RuntimeError(f"Gemini model {model} returned no image data")


def edit_image(
    styled_description: str,
    reference_image_bytes: bytes,
    image_model: str | None = None,
) -> bytes:
    """Edit an existing image using the styled description as guidance.

    Uses Gemini multimodal input (reference image + text prompt).
    Always returns PNG bytes.
    """
    model = image_model or settings.image_model

    logger.info(
        "Editing image with model=%s, aspect_ratio=%s, resolution=%s",
        model,
        settings.image_aspect_ratio,
        settings.image_resolution,
    )

    full_prompt = f"{_get_system_prompt()}\n\n{styled_description}"

    google_client = get_google_client()
    response = google_client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=reference_image_bytes, mime_type="image/png"),
            full_prompt,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=settings.image_aspect_ratio,
                image_size=settings.image_resolution,
            ),
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_bytes = normalize_to_png(part.inline_data.data)
            logger.info("Edited image: %d bytes", len(image_bytes))
            return image_bytes

    raise RuntimeError(f"Gemini model {model} returned no image data")
