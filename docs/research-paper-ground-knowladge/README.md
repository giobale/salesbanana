# PaperBanana directory package (agent-friendly)

This package splits the PaperBanana paper into section-scoped Markdown files so an agent can retrieve only what it needs.

## What's inside

- `original/` — the original HTML export (kept intact).
- `sections/` — main paper sections (00–10).
- `appendix/` — appendix sections and supporting rubrics/prompts.
- `manifest.json` — a machine-readable index (ids, titles, paths).

## Recommended agent retrieval pattern

1. Load `manifest.json` at startup.
2. When the user asks a question, do a lightweight search over section titles/ids (or a vector index built from the `.md` files).
3. Retrieve and read only the top 1–3 relevant files.
4. If you need figures/layout, open the `original/` HTML and jump to the nearest `[[PAGE n]]` marker referenced in the `.md`.

## Notes

- `[[PAGE n]]` markers indicate original PDF page boundaries.
- The `.md` files prioritize readability over layout fidelity.

