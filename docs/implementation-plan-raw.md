# SalesBanana — Technical Implementation Plan

This is the implementation plan for the SalesBanana solution, updated to reflect the current state of the project.

## System Overview

A pipeline that takes a natural-language brief about a diagram and produces a publication-ready illustration through orchestrated LLM calls, with a web UI for interactive use.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RUNTIME PIPELINE                             │
│                                                                     │
│  Brief ──→ [Retriever] ──→ [Planner] ──→ [Stylist] ──→ [Loop x3] ──→ Image
│               │                │              │         ┌────────┐  │
│               ▼                ▼              ▼         │Visualize│  │
│          Reference DB    Few-shot refs   Style Guide    │  ↕     │  │
│          (local JSON     injected as     (static .md)   │Critique │  │
│           + images)      context                        └────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component            | Tool                        | Why                                                  |
|----------------------|-----------------------------|------------------------------------------------------|
| **Orchestrator**     | Python 3.12+                | Direct OpenAI SDK calls, no framework overhead       |
| **LLM (text)**       | OpenAI GPT-4o via API       | Planning, critique, style application                |
| **Image generation** | OpenAI `gpt-image-1` (configurable) | Native multimodal generation from text descriptions |
| **Reference store**  | Local folder + `refs.json`  | No DB needed — category-based random selection       |
| **Config / prompts** | `.env` + YAML files         | Editable without code changes                        |
| **Settings**         | pydantic-settings           | Type-safe config loaded from `.env`                  |
| **Data models**      | Pydantic v2                 | Structured I/O between agents                        |
| **Web UI**           | FastAPI + Jinja2             | Browser-based brief entry and image viewing          |
| **Output**           | PNG (1536x1024 default)     | Timestamped run directories with all artifacts       |

### Image Generation Model Configuration

The image generation model is configurable via the `IMAGE_MODEL` env var in `.env`. The default is `gpt-image-1`.

| Env var | Default | Options |
|---------|---------|---------|
| `IMAGE_MODEL` | `gpt-image-1` | `gpt-image-1`, `dall-e-3` |
| `IMAGE_SIZE` | `1536x1024` | `1024x1024`, `1024x1536`, `1536x1024` |
| `IMAGE_QUALITY` | `high` | `low`, `medium`, `high` |

---

## Directory Structure

```
salesbanana/
├── config/
│   ├── README.md              # Component documentation
│   ├── style_guide.md         # Brand aesthetic guidelines
│   └── prompts.yaml           # All agent prompts (editable without code changes)
├── references/
│   ├── README.md              # Component documentation
│   ├── refs.json              # Metadata: {id, file, category, description, tags}
│   └── images/                # Reference diagram PNGs
├── src/
│   ├── __init__.py
│   ├── config.py              # Settings (pydantic-settings from .env), OpenAI client
│   ├── models.py              # Pydantic data models (Reference, PipelineResult, etc.)
│   ├── pipeline.py            # Main orchestrator
│   ├── agents/
│   │   ├── README.md          # Component documentation
│   │   ├── __init__.py
│   │   ├── retriever.py       # Reference selection (category classification)
│   │   ├── planner.py         # Brief → detailed visual description
│   │   ├── stylist.py         # Apply aesthetic guidelines from style_guide.md
│   │   ├── visualizer.py      # Generate image via OpenAI API
│   │   └── critic.py          # Multimodal evaluation + refinement
│   └── utils/
│       ├── README.md          # Component documentation
│       ├── __init__.py
│       ├── image_utils.py     # Base64 encoding, resizing, file I/O
│       └── prompt_loader.py   # Load and template YAML prompts
├── templates/
│   └── index.html             # Web UI (single page, embedded CSS + JS)
├── output/                    # Generated diagrams (timestamped run directories)
├── docs/
│   └── implementation-plan-raw.md
├── .env                       # Local config (gitignored)
├── .env.example               # Config template
├── .gitignore
├── README.md                  # Project overview with links to component docs
├── app.py                     # FastAPI web server
├── main.py                    # CLI entry point
└── requirements.txt
```

---

## Component Specifications

### 1. Reference Store (`references/`)

**One-time setup.** No vector database. No embeddings.

```json
[
  {
    "id": "ref_001",
    "file": "images/rag_pipeline_explainer.png",
    "category": "pipeline",
    "description": "Left-to-right RAG flow: user question input, search step, generation step...",
    "tags": ["pipeline", "concept-explainer", "rag", "llm"]
  }
]
```

**Categories** (6 total): `pipeline`, `staged_progression`, `canvas`, `comparison_cards`, `matrix`, `concept_explainer`

**Selection strategy**: Category match → random sample of `min(NUM_REFERENCES, available)`. Category match is sufficient — no embedding search needed.

---

### 2. Retriever Agent

```
Input:  brief (str)
Output: (list[Reference], category: str)

Logic:
  1. LLM classifies brief into one of 6 categories
  2. Filter refs.json by that category (fallback: all refs)
  3. Random sample of min(NUM_REFERENCES, available)
  4. Load base64 images for each selected reference
```

**Prompt** (`retriever_classify` in `prompts.yaml`):

| Requirement | Implementation |
|-------------|----------------|
| **Role** | Technical diagram analyst |
| **Task** | Classify brief into exactly ONE category |
| **Categories** | `pipeline`, `staged_progression`, `canvas`, `comparison_cards`, `matrix`, `concept_explainer` — each with a definition and usage guidance |
| **Output** | Single word (category name), no explanation |
| **Temperature** | 0.0 (deterministic) |

**Fallback**: If the LLM returns an invalid category, defaults to `pipeline`. Controlled by `VALID_CATEGORIES` set in `retriever.py`.

---

### 3. Planner Agent

```
Input:  brief (str) + refs (list[Reference] with base64 images)
Output: PlannerOutput (description: str, word_count: int)

Logic:
  1. Build multimodal message: text prompt + reference images (detail="low")
  2. LLM performs in-context learning from references
  3. Returns structured visual description (~500 words)
```

**Prompt** (`planner` in `prompts.yaml`):

| Requirement | Implementation |
|-------------|----------------|
| **Role** | Expert technical diagram planner for sales presentations |
| **Input placeholders** | `{brief}`, `{n}` (reference count), `{reference_descriptions}` |
| **Output sections** | COMPONENTS, LAYOUT, CONNECTIONS, GROUPING, DATA FLOW |
| **Specificity** | Must enable diagram recreation without the original brief |
| **Temperature** | 0.7 (creative generation) |

---

### 4. Stylist Agent

```
Input:  description (str)
Output: styled_description (str)

Logic:
  1. Load style_guide.md from config path
  2. Send description + style guide to LLM
  3. Returns enriched description with hex colors, px sizes, shape specs
```

**Prompt** (`stylist` in `prompts.yaml`):

| Requirement | Implementation |
|-------------|----------------|
| **Role** | Visual design expert applying brand guidelines |
| **Input placeholders** | `{visual_description}`, `{style_guide}` |
| **Preservation constraint** | Must not alter logical content — only add style directives |
| **Output target** | Optimized for image model comprehension |
| **Temperature** | 0.3 (faithful style application) |

---

### `style_guide.md` Specification

**Purpose**: Single-source-of-truth document for the visual identity of all generated diagrams. Injected verbatim into the Stylist prompt.

**Current sections** (164 lines):

| Section | Contents |
|---------|----------|
| **Brand Identity** | Audience and aesthetic framing (C-level, consulting context) |
| **Colour Palette** | 8 colors with hex codes, usage rules, gradient specs |
| **Typography** | Element-level specs (title, subtitle, body, labels), weight/color rules |
| **Layout Principles** | Spacing, alignment, 12-column grid, reading direction |
| **Shape Language** | Shape-to-usage mapping (rounded rect, circle, pill, dotted border, arrows) |
| **Iconography** | Line icons only, placement in circle containers, size specs |
| **Connectors and Flow** | Arrow thickness, color, direction, arrowhead style |
| **Card Variants** | Standard, gradient, and input/output box specs |
| **Definition & Takeaway Zones** | Bottom-section layout for concept explainers |
| **Anti-patterns** | 11 explicit "never do this" rules |

---

### 5. Visualizer Agent

```
Input:  styled_description (str)
Output: image_bytes (bytes)

Logic:
  Call OpenAI images.generate() with styled description as prompt.
  The styled description IS the prompt — no additional wrapping.
```

**Implementation:**
```python
response = client.images.generate(
    model=settings.image_model,          # From .env (default: "gpt-image-1")
    prompt=styled_description,
    size=settings.image_size.value,      # From .env (default: "1536x1024")
    quality=settings.image_quality.value, # From .env (default: "high")
    n=1,
    response_format="b64_json",
)
image_bytes = base64.b64decode(response.data[0].b64_json)
```

---

### 6. Critic Agent

```
Input:  image_bytes (bytes) + brief (str) + description (str)
Output: CriticOutput (approved: bool, refined_description: str | None, feedback_summary: str | None)

Logic:
  1. Send image (base64, detail="high") + brief + description to LLM
  2. Evaluate on 4 dimensions: Faithfulness, Conciseness, Readability, Aesthetics
  3. Returns "APPROVED" or a complete refined description
```

**Prompt** (`critic` in `prompts.yaml`):

| Requirement | Implementation |
|-------------|----------------|
| **Role** | QA reviewer for technical diagrams in sales presentations |
| **Input placeholders** | `{brief}`, `{description}`, image attached as base64 |
| **Evaluation rubric** | Faithfulness, Conciseness, Readability, Aesthetics |
| **Decision** | ALL pass → "APPROVED" on first line. ANY fail → complete refined description |
| **Refinement quality** | Specific corrections, standalone description (not a diff) |
| **Temperature** | 0.2 (consistent evaluation) |

---

## Data Models (`src/models.py`)

```python
Reference         # id, file, category, description, tags, image_base64
PlannerOutput     # description, word_count
CriticOutput      # approved, refined_description, feedback_summary
PipelineResult    # image_bytes, image_path, rounds_taken, approved, run_dir
RunMetadata       # brief, category, num_references, llm_model, image_model,
                  #   rounds_taken, approved, timestamp, elapsed_seconds
```

---

## Orchestration Flow (`src/pipeline.py`)

```python
def generate_diagram(brief: str, max_rounds: int | None = None) -> PipelineResult:

    # Setup
    rounds = max_rounds or settings.max_refinement_rounds
    run_dir = _create_run_dir()  # output/YYYYMMDD_HHMMSS/

    # Phase 1: Linear Planning
    refs, category = retriever.select_references(brief)
    planner_output = planner.create_description(brief, refs)
    styled_description = stylist.apply_style(planner_output.description)

    # Phase 2: Iterative Refinement
    for round_num in range(1, rounds + 1):
        image_bytes = visualizer.generate_image(current_description)
        critique = critic.evaluate(image_bytes, brief, current_description)

        if critique.approved:
            break
        current_description = critique.refined_description

    # Save final.png + run_metadata.json
    return PipelineResult(image_bytes, image_path, rounds_taken, approved, run_dir)
```

### State between agents:

```
Retriever  ──(refs + category)────────────→  Planner
Planner    ──(PlannerOutput.description)──→  Stylist
Stylist    ──(styled_description: str)────→  Visualizer ←──┐
Visualizer ──(image_bytes: bytes)─────────→  Critic        │
Critic     ──(CriticOutput.refined_description)────────────┘
                   (loops back to Visualizer, max N times)
```

### Output per run:

```
output/YYYYMMDD_HHMMSS/
├── 01_retriever_refs.json
├── 02_planner_description.md
├── 03_stylist_description.md
├── 04_round_N_image.png        (one per round)
├── 04_round_N_critique.md      (one per round)
├── final.png
└── run_metadata.json
```

---

## Entry Points

### CLI (`main.py`)

```bash
python main.py "A pipeline showing data flowing from Stripe through ETL into Snowflake"
python main.py --rounds 5 "..."
echo "..." | python main.py
```

Accepts brief as argument or stdin. Optional `--rounds` override.

### Web UI (`app.py` + `templates/index.html`)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serves the single-page UI |
| `/api/generate` | POST | `{"brief": "..."}` → runs pipeline in thread pool → returns `{image_url, rounds_taken, approved, run_dir}` |
| `/output/...` | GET | Static file serving for generated images |

**UI states**: Input (textarea + Generate button, Cmd+Enter shortcut) → Loading (spinner + step progress) → Result (image + metadata badges + Generate Another).

Pyne brand styling: `#6C63FF` purple, Inter font, white cards, 12px rounded corners.

---

## Configuration (`src/config.py`)

All settings loaded from `.env` via pydantic-settings `BaseSettings`.

| Env var | Default | Type | Purpose |
|---------|---------|------|---------|
| `OPENAI_API_KEY` | — | `str` | **Required** |
| `LLM_MODEL` | `gpt-4o` | `str` | Text agents (retriever, planner, stylist, critic) |
| `IMAGE_MODEL` | `gpt-image-1` | `str` | Image generation |
| `IMAGE_SIZE` | `1536x1024` | `ImageSize` enum | `1024x1024`, `1024x1536`, `1536x1024` |
| `IMAGE_QUALITY` | `high` | `ImageQuality` enum | `low`, `medium`, `high` |
| `MAX_REFINEMENT_ROUNDS` | `3` | `int` (1-10) | Visualizer-critic loop limit |
| `NUM_REFERENCES` | `5` | `int` (1-20) | References per run |
| `OUTPUT_DIR` | `output` | `Path` | Resolved relative to project root |
| `REFERENCES_DIR` | `references` | `Path` | Resolved relative to project root |
| `STYLE_GUIDE_PATH` | `config/style_guide.md` | `Path` | Resolved relative to project root |
| `PROMPTS_PATH` | `config/prompts.yaml` | `Path` | Resolved relative to project root |
| `LOG_LEVEL` | `INFO` | `str` | Python logging level |

Module-level singletons: `settings = Settings()`, `client = OpenAI(api_key=...)`.

---

## API Costs Per Diagram (Estimated)

| Agent      | Calls | Model                | Est. tokens   | Est. cost |
|------------|-------|----------------------|---------------|-----------|
| Retriever  | 1     | GPT-4o               | ~500          | $0.003    |
| Planner    | 1     | GPT-4o               | ~3,000 (images in context) | $0.02 |
| Stylist    | 1     | GPT-4o               | ~2,000        | $0.01     |
| Visualizer | 1-3   | gpt-image-1 (configurable) | —        | ~$0.04-0.12 |
| Critic     | 1-3   | GPT-4o               | ~2,000 × N (image input) | $0.03-0.08 |
| **Total**  |       |                      |               | **~$0.10-0.23** |

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OPENAI_API_KEY
```

### Dependencies (`requirements.txt`)

```
openai>=1.40.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pyyaml>=6.0
pillow>=10.0.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
jinja2>=3.1.0
python-multipart>=0.0.9
```

### Populating References

1. Add diagram PNGs to `references/images/`
2. Add matching entries to `refs.json` with category, description, and tags
3. Ensure categories match `VALID_CATEGORIES` in `src/agents/retriever.py` and the taxonomy in `config/prompts.yaml`

---

## Prompt Engineering Best Practices

### Prompt Structure Principles

| Principle | Application |
|-----------|-------------|
| **Role-Task-Format (RTF)** | Every prompt defines: (1) Role the LLM assumes, (2) Task to accomplish, (3) Format of expected output |
| **Constrained output spaces** | Use enums, taxonomies, or exact keywords (e.g., "APPROVED") to reduce ambiguity |
| **Chain-of-thought suppression** | For classification tasks, explicitly request "output only" to avoid reasoning verbosity |
| **Negative constraints** | Include explicit "do not" instructions to prevent common failure modes |
| **Structured input injection** | Use clear placeholders (`{brief}`, `{image}`) with consistent naming across all prompts |

### Multimodal Prompting (Vision Tasks)

| Principle | Application |
|-----------|-------------|
| **Image-text interleaving** | For Planner/Critic: place images inline with their descriptions, not at prompt end |
| **Reference framing** | Prefix reference images with "Learn the visual patterns from these examples:" |
| **Evaluation anchoring** | For Critic: provide the original brief as ground truth, not just the generated description |
| **Detail level control** | `detail="low"` for reference images (save tokens), `detail="high"` for critic evaluation |

### Output Quality Control

| Principle | Application |
|-----------|-------------|
| **Specificity over creativity** | Prompts emphasize exact values (hex codes, pixel sizes) over interpretable terms |
| **Completeness checks** | Planner prompt requires 5 mandatory sections; incomplete outputs are invalid |
| **Iterative refinement** | Critic loop allows configurable rounds of correction (default 3) |
| **Actionable feedback** | Critic must provide specific corrections, not general suggestions |
| **Temperature tuning** | 0.0 (retriever), 0.2 (critic), 0.3 (stylist), 0.7 (planner) — calibrated per task |

### Configuration Externalization

All prompts are stored in `config/prompts.yaml` to enable:
1. **Iteration without code changes**: Prompt tuning doesn't require redeployment
2. **Version control**: Prompt changes are tracked alongside code
3. **A/B testing**: Easy to swap prompt variants for experimentation
