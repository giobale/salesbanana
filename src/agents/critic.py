"""Critic agent: multimodal evaluation of generated diagrams."""

import json
import logging
import re

from src.config import client, settings
from src.models import CriticOutput
from src.utils.image_utils import bytes_to_base64
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)


def _parse_critic_response(text: str) -> tuple[bool, str | None, str]:
    """Parse structured JSON from critic response, with fallback for plain text.

    Returns (approved, revised_description, feedback_summary).
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        suggestions = data.get("critic_suggestions", "")
        revised = data.get("revised_description", "")

        approved = suggestions.strip().upper() == "APPROVED"
        revised_desc = None if approved else (revised if revised and revised != "No changes needed" else None)
        return approved, revised_desc, suggestions
    except (json.JSONDecodeError, AttributeError):
        logger.debug("Critic response is not valid JSON, falling back to text parsing")
        if text.strip().upper().startswith("APPROVED"):
            return True, None, "All dimensions passed"
        return False, text, text[:200]


def evaluate(
    image_bytes: bytes,
    brief: str,
    description: str,
    current_round: int = 1,
    max_rounds: int = 3,
) -> CriticOutput:
    """
    Evaluate a generated image against the original brief and description.

    Args:
        image_bytes: PNG bytes of the generated diagram.
        brief: Original user request.
        description: The styled description used to generate the image.
        current_round: Which iteration of the Visualizer-Critic loop (1-indexed).
        max_rounds: Total number of refinement iterations allowed.

    Returns CriticOutput with approved=True, or approved=False with a
    complete refined description that fixes identified issues.
    """
    image_b64 = bytes_to_base64(image_bytes)

    prompt_text = get_prompt(
        "critic",
        brief=brief,
        description=description,
        t=str(current_round),
        T=str(max_rounds),
    )

    content: list[dict] = [
        {"type": "text", "text": prompt_text},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_b64}",
                "detail": "high",  # High detail for quality evaluation
            },
        },
    ]

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": content}],
        temperature=0.2,  # Low temp for consistent evaluation
        max_tokens=3000,
    )

    result_text = response.choices[0].message.content.strip()
    approved, revised_desc, summary = _parse_critic_response(result_text)

    if approved:
        logger.info("Critic: APPROVED (round %d/%d)", current_round, max_rounds)
        return CriticOutput(approved=True, feedback_summary=summary)

    logger.info(
        "Critic: REFINEMENT NEEDED (round %d/%d, %d words)",
        current_round,
        max_rounds,
        len(result_text.split()),
    )
    return CriticOutput(
        approved=False,
        refined_description=revised_desc,
        feedback_summary=summary,
    )
