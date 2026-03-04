# CLAUDE.md — SalesBanana

## What This Is

SalesBanana is a text-to-infographic generation system for business consulting. It adapts the PaperBanana academic framework (NeurIPS 2025) into a commercial pipeline that produces branded infographics from natural language input.

The system uses **in-context learning only** — no model training occurs. A curated reference set teaches a VLM how to structure and style diagrams at inference time.

## Using the research paper ground knowledge

Research paper ground knowledge lives in:
- `docs/research-paper-ground-knowladge/` (same contents as `paperbanana_directory/`)
- Primary index: `docs/research-paper-ground-knowladge/manifest.json`

### Non-negotiable rule: paper first, product second
When implementing or modifying the pipeline:
1) **Paper-grounding pass (must do first)**
   - Open `manifest.json`
   - Select at most **3 relevant files**
   - Read and extract the **paper-spec**: inputs/outputs, algorithm steps, constraints, failure modes, hyperparameters
   - Cite decisions with `filename + anchor` when available

2) **Business adaptation pass (must do second)**
   - Propose **commercial customizations** (branding controls, template constraints, latency/cost tradeoffs, UX considerations, guardrails)
   - Clearly label what is:
     - **Paper-derived** (with citations)
     - **Product decision / assumption** (no citation, explain rationale)

### Default retrieval behavior
- Prefer Markdown in:
  - `docs/research-paper-ground-knowladge/sections/`
  - `docs/research-paper-ground-knowladge/appendix/`
- Use `docs/research-paper-ground-knowladge/original/` HTML only for figures/tables.

### Search workflow (no embeddings required)
- Start with ripgrep to route quickly:
  - `rg -n "keyword|synonym" docs/research-paper-ground-knowladge/sections docs/research-paper-ground-knowladge/appendix`
- Then open the best-matching file(s) and read surrounding headings.

### Stop condition
If the paper does not specify a needed detail:
- Say: **"Not specified in the paper."**
- Propose a sensible assumption and label it as a **product decision**.

## Architecture — Five Agents, One Pipeline

```
User Input → Retriever → Planner → Stylist → Visualizer ⇄ Critic → Final Output
                ↑             ↑         ↑                      ↑
            refs.json     selected  style_guide.md        brief + description
           (text only)  refs + imgs  (visual rules)         + rendered image
```

**Phase 1 — Planning** (linear): Retriever → Planner → Stylist. Each agent runs once.

**Phase 2 — Refinement** (iterative): Visualizer generates an image. Critic evaluates it. If not approved, the Critic returns a revised description and the Visualizer re-renders. Loop repeats up to `MAX_REFINEMENT_ROUNDS`.

Each agent has **one job**. It receives from the previous agent. It serves the next.

### Retriever

**Objective:** Select the N most structurally relevant references from the catalogue.

- Receives: user input + all reference metadata from `refs.json` (description + category + tags)
- Produces: ranked shortlist of N references (default N=10)
- Works on **text only** — never sees reference images
- Matches by **structural pattern and business domain**, never by visual style or topic keywords
- Does not plan, does not generate, does not style

### Planner

**Objective:** Produce a structured diagram specification from user input, guided by retrieved references.

- Receives: user input + N reference triplets (description, tags, image)
- Produces: a layout plan — element hierarchy, flow direction, content mapping, spatial arrangement
- This is the **only agent that sees reference images** — it learns structural patterns from them
- Does not retrieve, does not write code, does not apply brand styling

### Stylist

**Objective:** Apply brand-consistent visual styling to the Planner's structural specification.

- Receives: the Planner's structural description + `style_guide.md` + diagram category
- Produces: a fully styled description (continuous prose) optimized for the Visualizer
- Owns **all visual decisions**: colours, typography, spacing, shape language, iconography
- Preserves every logical element from the Planner — adds *how things look*, never changes *what things are*
- The style guide is the Stylist's sole authority — no other agent references it
- Does not retrieve, does not plan structure, does not evaluate output

### Visualizer

**Objective:** Render the styled description into a consulting-grade diagram image ready for slides or proposals.

- Receives: the Stylist's fully styled description (continuous prose) — this is the complete spec of what to draw
- Produces: a rendered PNG image that faithfully implements the description
- Owns **layout composition**: element placement for "executive scan" reading — clear hierarchy, top-left → bottom-right flow, strong grouping, whitespace
- Owns **visual encoding**: converts abstract relationships into visual structure — sequence → arrows/steps, responsibility → labelled columns, dependency → connectors, emphasis → callouts or highlight states
- Encoding must be **internally consistent**: same type of concept = same shape/colour treatment throughout the diagram
- Implements **exactly what the description specifies** — no invented components, no creative additions, no layout reinterpretation
- Every arrow must mean something; every label must be specific; no ambiguity
- No title inside the graphic — titles belong in slide headings, not in the rendered image
- Does not decide the business story (Planner's job), does not write style rules (Stylist's job), does not evaluate output (Critic's job)

### Critic

**Objective:** Evaluate the generated diagram against the original brief and description, then approve or revise.

- Receives: rendered image (PNG) + original user brief + the styled description used to generate it + loop position (round *t* of *T*)
- Produces: either `APPROVED` or a **revised description** that fixes identified issues
- This is the **only multimodal evaluation point** — it sees the generated image alongside the text inputs
- Evaluates four dimensions in priority order: **Faithfulness** (all requested elements present, none hallucinated) → **Readability** (labels legible, flow unambiguous) → **Conciseness** (no clutter) → **Aesthetics** (balanced layout)
- Includes a dedicated **text quality check**: misspellings, garbled characters, truncated words, overlapping or duplicated labels
- Includes a **generation failure check**: blank images, corruption, or error notices trigger automatic rejection with a simplified revision
- When revising, modifies the *existing* description with targeted fixes — never rewrites from scratch
- Revision must be **maximally specific**: exact element names, positions, corrections — vague feedback ("improve layout") is forbidden
- Does not select references, does not plan structure, does not generate images, does not apply style independently

## Separation of Concerns

This is the core design constraint. Every architectural decision flows from it.

| Concern | Owner | No Other Agent May |
|---|---|---|
| Reference selection | Retriever | Choose which references enter the context |
| Structural layout | Planner | Decide element hierarchy or flow direction |
| Visual branding | Stylist | Apply colours, fonts, spacing, or shape rules |
| Image generation | Visualizer | Produce or modify renderable output |
| Quality evaluation & revision | Critic | Approve output or rewrite the generation description |

**If you are unsure which agent owns a behaviour, it does not belong in the one you are writing.**

## Reference Set — `refs.json`

Each reference is a metadata record with three fields that serve distinct purposes:

```json
{
  "id": "ref_001",
  "file": "images/pipeline/example.png",
  "category": "pipeline",
  "description": "Multi-source ingestion flowing from 4 parallel inputs through transformation layer into single destination",
  "tags": ["pipeline", "concept-explainer", "input-output"]
}
```

### Field Responsibilities

**`description`** — Structural pattern in domain-agnostic language. Describes the *shape* of the diagram (element count, flow direction, spatial arrangement, containment relationships). Never contains technology names, brand terms, or topic-specific jargon. This is what the Retriever reads to match against user input.

**`category`** — High-level structural archetype. Accelerates retrieval matching. Current categories: `pipeline`, `canvas`, `staged-progression`, `matrix`, `comparison-cards`.

**`tags`** — Secondary structural and layout signals. Combine category with finer-grained pattern descriptors. Never include style terms (colours, fonts) or domain-specific terms.

### Why Domain-Agnostic

The PaperBanana ablation study showed random retrieval ≈ semantic retrieval in performance. This means structural pattern exposure matters more than topic matching. Descriptions that contain domain terms (e.g. "BigQuery", "API", "data pipeline") would leak reference-domain vocabulary into generation, causing the model to hallucinate those terms in unrelated outputs.

References teach **how to structure** information visually. User input provides **what content** to structure. These must never mix.

## Style Guide — `style_guide.md`

Encodes the complete Pyne visual identity: colour palette, typography, layout grid, shape language, iconography, connectors, card variants, and anti-patterns.

**Only the Stylist reads this file.** No other agent should reference, embed, or be influenced by style guide contents. If style information appears in a Retriever prompt, a Planner specification, or Critic revision — that is a bug.

## Rules for Coding Agents

1. **Do not merge agent responsibilities.** A single prompt or function that retrieves, plans, and styles is a violation of the architecture. Agents are separate units with separate prompts and separate I/O contracts.

2. **Do not put style in descriptions.** Reference descriptions in `refs.json` describe structure. Colour, font, spacing, and brand terms belong in `style_guide.md` and nowhere else.

3. **Do not put structure in the style guide.** The style guide defines how things look, not what elements exist or how they connect. Layout *principles* (grid, alignment) are style. Layout *decisions* (this diagram has 4 cards in a row) are structure owned by the Planner.

4. **Do not hardcode reference selection.** The Retriever selects references at runtime based on user input. No agent should assume which references will be available or embed specific reference IDs.

5. **Do not let the Visualizer improvise.** The Visualizer renders the styled description exactly as written. If the spec says 3 cards, the output has 3 cards. Creative additions are the Planner's job; visual styling is the Stylist's job.

6. **Do not bypass the pipeline.** Every generation passes through all five agents in order. No shortcut from user input to image. No shortcut from plan to styled output. The Critic must evaluate every generated image.

7. **Do not let the Critic make vague revisions.** The Critic's revised description must contain exact element names, positions, and corrections. Feedback like "improve the layout" or "make it cleaner" degrades the next generation. If the Critic cannot be specific, it should approve.

8. **Do not let the Critic change the design system.** The Critic may not alter colour palettes, font choices, or brand styling unless a specific style choice directly causes a readability failure. Aesthetic consistency is the Stylist's domain.

9. **Keep descriptions structural.** When adding references to `refs.json`, describe what you see in terms of element count, spatial arrangement, flow direction, containment, and hierarchy — never in terms of the business topic depicted.

10. **Keep categories in sync across all three sources.** When adding a new category to `refs.json`, you **must** also add it to `VALID_CATEGORIES` in `src/agents/retriever.py` and to the `CATEGORY TAXONOMY` section in `config/prompts.yaml`. All three must list the same set of categories. A category that exists in only one or two of these locations is a bug.

## Workflow Orchestration

### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimat Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
