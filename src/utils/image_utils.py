"""Image encoding, resizing, and file I/O utilities."""

import base64
import logging
from io import BytesIO
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


def image_to_base64(image_path: Path, max_dimension: int = 1024) -> str:
    """
    Read an image file, resize if needed, return base64-encoded PNG string.

    Used for injecting reference images into multimodal prompts.
    Resizes so the largest dimension is at most `max_dimension` pixels.
    """
    img = Image.open(image_path)
    original_size = img.size

    if max(img.size) > max_dimension:
        ratio = max_dimension / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        logger.debug(
            "Resized %s from %s to %s", image_path.name, original_size, new_size
        )

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def normalize_to_png(image_bytes: bytes) -> bytes:
    """Convert any supported image format (WEBP, JPEG, etc.) to PNG bytes."""
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def bytes_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def save_image(image_bytes: bytes, output_path: Path) -> Path:
    """Save image bytes to disk. Returns the path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    logger.info("Saved image to %s (%d bytes)", output_path, len(image_bytes))
    return output_path
