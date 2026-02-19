"""Main orchestrator: wires all agents together, manages the refinement loop."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from src.agents import critic, planner, retriever, stylist, visualizer
from src.config import settings
from src.models import PipelineResult, RunMetadata
from src.postprocessing import adapt_for_slides
from src.utils.image_utils import save_image

logger = logging.getLogger(__name__)


def _create_run_dir() -> Path:
    """Create a timestamped directory for this run's outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = settings.output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _save_text(run_dir: Path, filename: str, content: str) -> None:
    """Save a text artifact to the run directory."""
    path = run_dir / filename
    with open(path, "w") as f:
        f.write(content)


def generate_diagram(
    brief: str,
    max_rounds: int | None = None,
    slide_format: str = "original",
    image_model: str | None = None,
) -> PipelineResult:
    """
    Execute the full pipeline:
        Brief -> Retriever -> Planner -> Stylist -> Visualizer <-> Critic -> Image

    Args:
        brief: Natural-language description of the desired diagram.
        max_rounds: Override max refinement rounds (default: from .env).

    Returns:
        PipelineResult with final image, path, and metadata.
    """
    rounds = max_rounds or settings.max_refinement_rounds
    start_time = time.time()
    run_dir = _create_run_dir()

    logger.info("=== Pipeline started === Run dir: %s", run_dir)
    logger.info("Brief: %s", brief[:100] + "..." if len(brief) > 100 else brief)

    # ── Phase 1: Linear Planning ──────────────────────────────────────

    # Step 1: Retrieve references
    logger.info("--- Step 1: Retriever ---")
    refs, category = retriever.select_references(brief)
    refs_metadata = [r.model_dump(exclude={"image_base64"}) for r in refs]
    _save_text(run_dir, "01_retriever_refs.json", json.dumps(refs_metadata, indent=2))

    # Step 2: Plan visual description
    logger.info("--- Step 2: Planner ---")
    planner_output = planner.create_description(brief, refs)
    _save_text(run_dir, "02_planner_description.md", planner_output.description)

    # Step 3: Apply style
    logger.info("--- Step 3: Stylist ---")
    styled_description = stylist.apply_style(planner_output.description, category)
    _save_text(run_dir, "03_stylist_description.md", styled_description)

    # ── Phase 2: Iterative Refinement ─────────────────────────────────

    current_description = styled_description
    final_image_bytes = None
    approved = False
    rounds_taken = 0

    for round_num in range(1, rounds + 1):
        logger.info(
            "--- Round %d/%d: Visualizer ---", round_num, rounds
        )

        # Generate image
        image_bytes = visualizer.generate_image(current_description, image_model=image_model)
        save_image(image_bytes, run_dir / f"04_round_{round_num}_image.png")
        final_image_bytes = image_bytes
        rounds_taken = round_num

        # Critique
        logger.info("--- Round %d/%d: Critic ---", round_num, rounds)
        critique = critic.evaluate(
            image_bytes=image_bytes,
            brief=brief,
            description=current_description,
            current_round=round_num,
            max_rounds=rounds,
        )

        if critique.approved:
            approved = True
            _save_text(run_dir, f"04_round_{round_num}_critique.md", "APPROVED")
            logger.info("Image approved on round %d", round_num)
            break

        _save_text(
            run_dir,
            f"04_round_{round_num}_critique.md",
            critique.refined_description or "",
        )
        current_description = critique.refined_description
        logger.info("Round %d: refinement needed, continuing...", round_num)

    if not approved:
        logger.warning(
            "Max rounds (%d) exhausted without approval. Using last generated image.",
            rounds,
        )

    # ── Save final outputs ────────────────────────────────────────────

    if slide_format != "original":
        save_image(final_image_bytes, run_dir / "final_raw.png")
        final_image_bytes = adapt_for_slides(final_image_bytes, slide_format)

    final_path = save_image(final_image_bytes, run_dir / "final.png")

    elapsed = time.time() - start_time
    metadata = RunMetadata(
        brief=brief,
        category=category,
        num_references=len(refs),
        llm_model=settings.llm_model,
        image_model=image_model or settings.image_model,
        rounds_taken=rounds_taken,
        approved=approved,
        timestamp=datetime.now().isoformat(),
        elapsed_seconds=round(elapsed, 2),
    )
    _save_text(run_dir, "run_metadata.json", metadata.model_dump_json(indent=2))

    logger.info(
        "=== Pipeline completed === Rounds: %d, Approved: %s, Time: %.1fs",
        rounds_taken,
        approved,
        elapsed,
    )

    return PipelineResult(
        image_bytes=final_image_bytes,
        image_path=final_path,
        rounds_taken=rounds_taken,
        approved=approved,
        run_dir=run_dir,
    )
