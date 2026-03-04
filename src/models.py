"""Pydantic data models used across the pipeline."""

from pathlib import Path

from pydantic import BaseModel, Field


class Reference(BaseModel):
    """A single reference diagram from the references/ directory."""

    id: str
    file: str  # Relative path within references/ (e.g. "images/pipeline/rag_pipeline_explainer.png")
    category: str
    description: str
    tags: list[str] = Field(default_factory=list)
    image_base64: str | None = None  # Populated at runtime by retriever


class PlannerOutput(BaseModel):
    """Structured output from the Planner agent."""

    description: str  # ~500 word visual description
    word_count: int


class CriticOutput(BaseModel):
    """Output from the Critic agent."""

    approved: bool
    refined_description: str | None = None  # None if approved
    feedback_summary: str | None = None  # Human-readable summary


class PipelineResult(BaseModel):
    """Final result of the entire pipeline."""

    model_config = {"arbitrary_types_allowed": True}

    image_bytes: bytes
    image_path: Path
    rounds_taken: int
    approved: bool  # False if max rounds exhausted without approval
    run_dir: Path  # Where intermediate files are saved


class RunMetadata(BaseModel):
    """Metadata about a pipeline run, saved to run_metadata.json."""

    brief: str
    category: str
    num_references: int
    llm_model: str
    image_model: str
    rounds_taken: int
    approved: bool
    timestamp: str
    elapsed_seconds: float
