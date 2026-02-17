# CLAUDE.md — SalesBanana

## What This Is

SalesBanana is a text-to-infographic generation system for business consulting. It adapts the PaperBanana academic framework (NeurIPS 2025) into a commercial pipeline that produces branded infographics from natural language input.

The system uses **in-context learning only** — no model training occurs. A curated reference set teaches a VLM how to structure and style diagrams at inference time.

## Architecture — Four Agents, One Pipeline

```
User Input → Retriever → Planner → Coder → Stylist → Final Output
                ↑             ↑                          ↑
            refs.json     selected refs            style_guide.md
           (text only)     (with images)          (visual rules)
```

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

### Coder

**Objective:** Translate the Planner's specification into renderable output.

- Receives: the Planner's structured layout plan
- Produces: code (SVG, HTML, or target format) that faithfully implements the plan
- Implements **exactly what the Planner specified** — no creative additions, no layout reinterpretation
- Does not retrieve, does not plan, does not style

### Stylist

**Objective:** Apply brand-consistent visual styling to the Coder's output.

- Receives: raw rendered output from the Coder + `style_guide.md`
- Produces: final branded infographic
- Owns **all visual decisions**: colours, typography, spacing, shape language, iconography
- The style guide is the Stylist's sole authority — no other agent references it
- Does not retrieve, does not plan structure, does not rewrite code logic

## Separation of Concerns

This is the core design constraint. Every architectural decision flows from it.

| Concern | Owner | No Other Agent May |
|---|---|---|
| Reference selection | Retriever | Choose which references enter the context |
| Structural layout | Planner | Decide element hierarchy or flow direction |
| Code generation | Coder | Produce or modify renderable output |
| Visual branding | Stylist | Apply colours, fonts, spacing, or shape rules |

**If you are unsure which agent owns a behaviour, it does not belong in the one you are writing.**

## Reference Set — `refs.json`

Each reference is a metadata record with three fields that serve distinct purposes:

```json
{
  "id": "ref_001",
  "file": "images/example.png",
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

**Only the Stylist reads this file.** No other agent should reference, embed, or be influenced by style guide contents. If style information appears in a Retriever prompt, a Planner specification, or Coder logic — that is a bug.

## Rules for Coding Agents

1. **Do not merge agent responsibilities.** A single prompt or function that retrieves, plans, and styles is a violation of the architecture. Agents are separate units with separate prompts and separate I/O contracts.

2. **Do not put style in descriptions.** Reference descriptions in `refs.json` describe structure. Colour, font, spacing, and brand terms belong in `style_guide.md` and nowhere else.

3. **Do not put structure in the style guide.** The style guide defines how things look, not what elements exist or how they connect. Layout *principles* (grid, alignment) are style. Layout *decisions* (this diagram has 4 cards in a row) are structure owned by the Planner.

4. **Do not hardcode reference selection.** The Retriever selects references at runtime based on user input. No agent should assume which references will be available or embed specific reference IDs.

5. **Do not let the Coder improvise.** The Coder implements the Planner's spec. If the spec says 3 cards, the output has 3 cards. Creative additions are the Planner's job.

6. **Do not bypass the pipeline.** Every generation passes through all four stages in order. No shortcut from user input to code. No shortcut from plan to styled output.

7. **Keep descriptions structural.** When adding references to `refs.json`, describe what you see in terms of element count, spatial arrangement, flow direction, containment, and hierarchy — never in terms of the business topic depicted.