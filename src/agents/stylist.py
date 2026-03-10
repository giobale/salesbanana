"""Stylist agent: enrich visual description with style guide directives."""

import logging

from src.config import client, settings
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)


def _load_style_guide() -> str:
    """Load the style guide markdown file."""
    with open(settings.style_guide_path, "r") as f:
        return f.read()


def apply_style(visual_description: str, category: str = "") -> str:
    """
    Rewrite the visual description with explicit style directives
    from the style guide (hex colors, shapes, typography, connector styles).
    """
    style_guide = _load_style_guide()

    prompt = get_prompt(
        "stylist",
        visual_description=visual_description,
        category=category,
        style_guide=style_guide,
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # Lower temp for faithful style application
        max_tokens=3000,
    )

    styled = response.choices[0].message.content.strip()
    logger.info("Stylist produced styled description: %d words", len(styled.split()))

    return styled


def restyle(styled_description: str, category: str = "") -> str:
    """
    Validate and refresh styling on an already-styled description after a
    content merge. Fills gaps on new elements, fixes drift, preserves
    existing correct styling.
    """
    style_guide = _load_style_guide()

    prompt = get_prompt(
        "stylist_restyle",
        styled_description=styled_description,
        category=category,
        style_guide=style_guide,
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=3000,
    )

    restyled = response.choices[0].message.content.strip()
    logger.info("Stylist restyle produced description: %d words", len(restyled.split()))

    return restyled
