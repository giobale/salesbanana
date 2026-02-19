"""Visualizer agent: generate an image from the styled description."""

import base64
import logging

from src.config import IMAGE_MODELS, client, get_google_client, settings
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


def _generate_openai(model: str, prompt: str) -> bytes:
    """Generate an image via the OpenAI Images API."""
    quality = settings.image_quality.value
    size = settings.image_size.value

    if model.startswith("dall-e"):
        # DALL-E 3 only accepts "standard" and "hd"
        quality = "hd" if quality == "high" else "standard"
        # DALL-E 3 sizes: 1024x1024, 1024x1792, 1792x1024
        dalle_size_map = {"1024x1536": "1024x1792", "1536x1024": "1792x1024"}
        size = dalle_size_map.get(size, size)

    kwargs = dict(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )
    if model.startswith("dall-e"):
        kwargs["response_format"] = "b64_json"

    response = client.images.generate(**kwargs)
    image_base64 = response.data[0].b64_json
    return normalize_to_png(base64.b64decode(image_base64))


def _generate_google(model: str, prompt: str) -> bytes:
    """Generate an image via the Google GenAI API. Returns PNG bytes."""
    from google.genai import types

    google_client = get_google_client()
    response = google_client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            # Gemini returns WEBP/JPEG; normalize to PNG for pipeline consistency
            return normalize_to_png(part.inline_data.data)
    raise RuntimeError(f"Gemini model {model} returned no image data")


def generate_image(styled_description: str, image_model: str | None = None) -> bytes:
    """
    Generate an image using the specified (or default) image generation model.

    Routes to the correct provider (OpenAI or Google) based on the IMAGE_MODELS
    registry. Always returns PNG bytes regardless of provider.
    """
    model = image_model or settings.image_model
    provider = IMAGE_MODELS[model]["provider"]

    logger.info(
        "Generating image with model=%s, provider=%s, size=%s, quality=%s",
        model,
        provider,
        settings.image_size.value,
        settings.image_quality.value,
    )

    full_prompt = f"{_get_system_prompt()}\n\n{styled_description}"

    if provider == "openai":
        image_bytes = _generate_openai(model, full_prompt)
    elif provider == "google":
        image_bytes = _generate_google(model, full_prompt)
    else:
        raise ValueError(f"Unknown provider '{provider}' for model '{model}'")

    logger.info("Generated image: %d bytes", len(image_bytes))
    return image_bytes
