"""Main orchestrator: wires all agents together, manages the refinement loop."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from src.agents import critic, planner, retriever, stylist, visualizer
from src.config import client, settings
from src.models import ImprovementResult, ImprovementRound, PipelineResult, RunMetadata
from src.utils.image_utils import save_image
from src.utils.prompt_loader import get_prompt

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

    # Save the description that produced the final image
    _save_text(run_dir, "04_final_description.md", current_description)

    # ── Save final outputs ────────────────────────────────────────────

    save_image(final_image_bytes, run_dir / "00_original_image.png")
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


# ── Improvement Loop ──────────────────────────────────────────────────


_MAX_HISTORY_IN_PROMPT = 10


def _load_improvements(run_dir: Path) -> list[ImprovementRound]:
    """Load existing improvement history from run_dir, or return empty list."""
    path = run_dir / "improvements.json"
    if not path.exists():
        return []
    with open(path) as f:
        return [ImprovementRound(**r) for r in json.loads(f.read())]


def _save_improvements(run_dir: Path, history: list[ImprovementRound]) -> None:
    """Persist the full improvement history to improvements.json."""
    data = [r.model_dump() for r in history]
    _save_text(run_dir, "improvements.json", json.dumps(data, indent=2))


def _get_last_description(run_dir: Path, history: list[ImprovementRound]) -> str:
    """Get the description that produced the most recent image."""
    if history:
        last = history[-1]
        path = run_dir / f"05_improvement_{last.round_number}_description.md"
        return path.read_text()
    return (run_dir / "04_final_description.md").read_text()


def _get_last_image_bytes(run_dir: Path, history: list[ImprovementRound]) -> bytes:
    """Get the bytes of the most recent image."""
    if history:
        last = history[-1]
        path = run_dir / last.image_filename
    else:
        original = run_dir / "00_original_image.png"
        path = original if original.exists() else run_dir / "final.png"
    return path.read_bytes()


def _format_history_for_prompt(history: list[ImprovementRound]) -> str:
    """Format improvement history as numbered text for LLM context."""
    if not history:
        return "No previous improvements."
    recent = history[-_MAX_HISTORY_IN_PROMPT:]
    lines = []
    for r in recent:
        lines.append(f"#{r.round_number}: {r.summary}")
    return "\n".join(lines)


def _generate_summary(instruction: str) -> str:
    """Generate a 1-sentence summary of a user improvement instruction."""
    prompt = get_prompt("improvement_summary", instruction=instruction)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=50,
    )
    return response.choices[0].message.content.strip()


def _merge_description(description: str, instruction: str, history_text: str) -> str:
    """Merge a user instruction into the existing styled description."""
    prompt = get_prompt(
        "improvement_merge",
        description=description,
        instruction=instruction,
        history=history_text,
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


def improve_diagram(
    run_dir: Path,
    instruction: str,
    image_model: str | None = None,
    branch_from_round: int | None = None,
) -> ImprovementResult:
    """
    Apply a user-driven improvement to an existing diagram.

    Loads context from the run directory, merges the instruction into the
    description, generates a new image via edit, and evaluates with the critic.

    Args:
        run_dir: Path to the existing run's output directory.
        instruction: Natural-language description of the desired change.
        image_model: Override image model (default: from run metadata or settings).

    Returns:
        ImprovementResult with the new image and updated history.
    """
    # Validate run_dir is under output_dir
    try:
        run_dir.resolve().relative_to(settings.output_dir.resolve())
    except ValueError:
        raise ValueError(f"Invalid run directory: {run_dir}")

    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    logger.info("=== Improvement started === Run dir: %s", run_dir)

    # Load context
    metadata_path = run_dir / "run_metadata.json"
    with open(metadata_path) as f:
        run_meta = json.loads(f.read())
    brief = run_meta["brief"]

    history = _load_improvements(run_dir)

    # Branch from history: truncate to the selected round
    if branch_from_round is not None:
        if branch_from_round < 0:
            raise ValueError(f"Invalid branch_from_round: {branch_from_round}")
        if branch_from_round == 0:
            history = []
        else:
            history = [r for r in history if r.round_number <= branch_from_round]
            if not history or history[-1].round_number != branch_from_round:
                raise ValueError(
                    f"Round {branch_from_round} not found in improvement history"
                )
        _save_improvements(run_dir, history)
        logger.info("Branched from round %d, history truncated to %d items", branch_from_round, len(history))

    last_description = _get_last_description(run_dir, history)
    last_image_bytes = _get_last_image_bytes(run_dir, history)
    round_number = (max(r.round_number for r in history) + 1) if history else 1

    logger.info("Improvement round %d, instruction: %s", round_number, instruction[:80])

    # Generate summary
    summary = _generate_summary(instruction)
    logger.info("Summary: %s", summary)

    # Merge instruction into description
    history_text = _format_history_for_prompt(history)
    merged_description = _merge_description(last_description, instruction, history_text)
    logger.info("Description merged (%d words)", len(merged_description.split()))

    # Generate improved image
    logger.info("--- Improvement %d: Visualizer (edit) ---", round_number)
    new_image_bytes = visualizer.edit_image(
        merged_description, last_image_bytes, image_model=image_model
    )

    # Critic evaluation
    logger.info("--- Improvement %d: Critic ---", round_number)
    critique = critic.evaluate_improvement(
        image_bytes=new_image_bytes,
        previous_image_bytes=last_image_bytes,
        brief=brief,
        description=merged_description,
        instruction=instruction,
    )

    current_description = merged_description
    approved = critique.approved

    # One auto-retry if critic rejects
    if not approved and critique.refined_description:
        logger.info("--- Improvement %d: Auto-retry with critic revision ---", round_number)
        current_description = critique.refined_description
        new_image_bytes = visualizer.edit_image(
            current_description, last_image_bytes, image_model=image_model
        )
        retry_critique = critic.evaluate_improvement(
            image_bytes=new_image_bytes,
            previous_image_bytes=last_image_bytes,
            brief=brief,
            description=current_description,
            instruction=instruction,
        )
        approved = retry_critique.approved
        critique = retry_critique

    # Save artifacts
    final_image_bytes = new_image_bytes
    img_filename = f"05_improvement_{round_number}_image.png"
    save_image(new_image_bytes, run_dir / img_filename)
    _save_text(run_dir, f"05_improvement_{round_number}_description.md", current_description)
    _save_text(
        run_dir,
        f"05_improvement_{round_number}_critique.md",
        "APPROVED" if approved else (critique.feedback_summary or ""),
    )

    # Update final.png
    save_image(final_image_bytes, run_dir / "final.png")

    # Record this round
    improvement = ImprovementRound(
        round_number=round_number,
        user_instruction=instruction,
        summary=summary,
        description_used=current_description,
        approved=approved,
        critic_feedback=critique.feedback_summary if not approved else None,
        image_filename=img_filename,
        timestamp=datetime.now().isoformat(),
    )
    history.append(improvement)
    _save_improvements(run_dir, history)

    logger.info(
        "=== Improvement %d completed === Approved: %s",
        round_number,
        approved,
    )

    return ImprovementResult(
        image_bytes=final_image_bytes,
        image_path=run_dir / "final.png",
        round_number=round_number,
        summary=summary,
        approved=approved,
        history=history,
        run_dir=run_dir,
    )
