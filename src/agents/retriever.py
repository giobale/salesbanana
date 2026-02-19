"""Retriever agent: classify brief into diagram category, select matching references."""

import json
import logging
import random

from src.config import client, settings
from src.models import Reference
from src.utils.image_utils import image_to_base64
from src.utils.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "pipeline",
    "staged-progression",
    "canvas",
    "comparison-cards",
    "matrix",
    "wheel",
    "concept-explainer",
}


def _load_refs() -> list[Reference]:
    """Load refs.json from the references directory."""
    refs_path = settings.references_dir / "refs.json"
    with open(refs_path, "r") as f:
        data = json.load(f)
    return [Reference(**item) for item in data]


def _classify_brief(brief: str) -> str:
    """Use LLM to classify the brief into a diagram category."""
    prompt = get_prompt("retriever_classify", brief=brief)

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=20,
    )

    category = response.choices[0].message.content.strip().lower()

    if category not in VALID_CATEGORIES:
        logger.warning(
            "LLM returned invalid category '%s', defaulting to 'pipeline'",
            category,
        )
        category = "pipeline"

    logger.info("Brief classified as category: %s", category)
    return category


def select_references(brief: str) -> tuple[list[Reference], str]:
    """
    Classify brief and return matching reference diagrams with base64 images.

    Returns:
        Tuple of (selected references with images loaded, classified category).
    """
    category = _classify_brief(brief)
    all_refs = _load_refs()

    matching = [r for r in all_refs if r.category == category]

    if not matching:
        logger.warning(
            "No refs for category '%s', falling back to all refs", category
        )
        matching = all_refs

    n = min(settings.num_references, len(matching))
    selected = random.sample(matching, n)

    # Load base64 images for each selected reference
    for ref in selected:
        image_path = settings.references_dir / ref.file
        if image_path.exists():
            ref.image_base64 = image_to_base64(image_path)
        else:
            logger.warning("Reference image not found: %s", image_path)

    logger.info("Selected %d references for category '%s'", len(selected), category)
    return selected, category
