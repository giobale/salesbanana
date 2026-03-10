# Infographic Style Guide — SalesBanana

## Brand Identity

All generated diagrams must match the visual identity of Pyne materials. The aesthetic is **clean, minimal, and Nordic professional** — designed for C-level and senior leadership audiences in a consulting context. The visual language says: "We are structured thinkers who make complex things simple."

---

## Canvas Format

- All infographics are **wide horizontal 16:9 landscape** format
- Background is always **white (`#FFFFFF`)** — never dark-mode, never coloured

---

## Colour Palette

| Role | Hex | Usage |
|---|---|---|
| Pyne Purple (Primary) | `#4F47E6` | Titles, subtitles, highlight labels, active states, key callouts |
| Pyne Purple Light | `#EEEDFC` | Callout boxes, light purple fills, hover states |
| Pyne Purple Dark | `#3F39B8` | Pressed states, gradient endpoints, emphasis accents |
| Text Primary | `#0A0A0A` | Body text, headings, strong containers |
| Text Secondary | `#374151` | Supporting text, descriptions |
| Text Muted | `#6B7280` | Tertiary text, placeholders, captions |
| Background | `#FAFAFA` | Card backgrounds, definition boxes, section fills |
| White | `#FFFFFF` | Canvas background, card surfaces |
| Border | `#E5E7EB` | Card borders, dividers, subtle separators |
| Success | `#10B981` / `#ECFDF5` | Positive indicators, confirmation states |
| Error | `#DC2626` / `#FEE2E2` | Error indicators, warning states |
| Warning | `#F59E0B` / `#FEF3C7` | Caution indicators, attention states |
| Steel blue | `#8C9BAA` | Tertiary card variant, muted accents |
| Gradient — purple | `#4F47E6 → #3F39B8` | Left-most or primary card in comparison layouts |
| Gradient — dark | `#2D2D3F → #1A1A2E` | Second card in comparison layouts |
| Gradient — steel | `#8C9BAA → #6B7280` | Third/fourth card in comparison layouts |

### Colour Principle
**Use colour to encode meaning, not to decorate.** Every distinct fill or accent colour in a diagram must serve a structural purpose — grouping related elements, signalling hierarchy, or distinguishing categories. If a colour choice doesn't help the viewer understand the diagram's logic, remove it.

### Colour Rules
- Never use more than **three distinct fills** in a single diagram (excluding white and light gray)
- Purple is always the **lead accent** — use it for the first element, the most important label, or the primary callout
- Dark and steel tones serve as **supporting fills** and never compete with purple for attention
- Background is always **white** — never dark-mode diagrams
- Avoid saturated reds, greens, or blues outside the palette
- Purple accent is applied **selectively** — only on: title keywords, icon fills inside active elements, subtitle phrases, question/callout boxes, checkmarks, and number badges. Never used for full paragraphs, borders, or large background areas

---

## Typography

### Font Family
**Primary font: Inter** (fallback: Plus Jakarta Sans). All text on every infographic — headings, body, labels — uses Inter. No other typeface is permitted.

| Element | Style |
|---|---|
| Diagram title | Large sans-serif (≈36–44pt equivalent), mixed colour: purple for the key phrase, black for the rest |
| Section subtitle | ALL CAPS, small (≈10pt), letter-spacing 2–3px, gray or black |
| Card title | Bold sans-serif, 16–20pt, black or purple |
| Card subtitle / guiding question | Regular weight, purple, 12–14pt, used to frame the purpose of a section |
| Body text | Regular weight, dark gray (#6B7280), 11–13pt, max 2–3 lines per block |
| Definition label | Bold "Definition:" prefix followed by regular-weight text |
| Number labels | Extra-large bold (≈48–64pt), used inside staged-progression and comparison-card layouts |
| Emphasis | Bold individual words within body text for key terms (e.g., "data", "models", "deployment") — never italic, never underline |

### Title Pattern
Every diagram title follows a **split-colour pattern**:
- The **topic keyword or phrase** is rendered in purple (`#4F47E6`)
- The **contextual/descriptive remainder** is rendered in black (`#0A0A0A`)
- Examples: *"Retrieval Augmented Generation (RAG):* Giving GenAI your business knowledge" — purple portion first, black portion second
- Colon or line break separates the two portions
- Title is always **top-left aligned**, never centred

### Typography Rules
- Maximum **two font weights** per diagram: regular and bold
- No italic anywhere except guiding questions in canvas layouts
- Purple text is reserved for **subtitles and callout phrases** — never full paragraphs
- ALL CAPS only for small section labels (≈10pt or below)
- All text uses **Inter** (or Plus Jakarta Sans) throughout — no serif, monospace, or decorative fonts

---

## Layout Principles

### Spacing
- Generous padding from canvas edges: **48–64px** on all sides
- Consistent internal padding in all containers: ≈20–30px equivalent
- Equal gaps between cards/phases in any row (no variable spacing)
- Clear vertical separation between the diagram zone and the definition/takeaway zone

### Alignment
- Horizontal left-to-right is the dominant reading direction
- Titles always top-left aligned
- Content is **centred within cards** but the overall composition is **left-anchored**

### Grid
- Diagrams are laid out on an implicit **12-column grid**
- Cards and phases always have equal widths within a row
- Definition boxes span roughly 1/3 width, positioned bottom-left
- Takeaway or comparison boxes span the remaining 2/3, bottom-right

---

## Shape Language

| Shape | Usage |
|---|---|
| Rounded rectangle (r ≈ 8–16px) | Cards, containers, input/output boxes, definition boxes |
| Circle | Icon containers, phase number badges, hub nodes in pinwheel layouts |
| Pill / stadium shape | Tall comparison cards (Five Questions style) |
| Dotted border | Trigger events, input containers, definition boxes — signals "context" or "boundary" |
| Solid thin border (1–1.5px) | Canvas grids, framework containers |
| Arrow (thin, ≈1.5px) | Flow direction between steps — straight and horizontal for primary linear flow |
| Arrow (bold) | Used only for canvas layouts pointing toward Impact/Insights |

### Shape Rules
- White cards use **subtle shadows** for depth — keep shadows faint and consistent (≈2–4px blur, 5–10% opacity)
- **No 3D effects** anywhere
- Borders are either **solid thin black/gray** or **dotted gray** — never coloured borders
- Rounded corners are consistent: always the same radius within a single diagram

---

## Iconography

- Style: **line icons only** — thin stroke (1.5–2px), monochrome
- Colour: black or dark gray by default; purple when inside an active/primary element
- Placement: always **centred inside a circle container** (light gray fill, no border or subtle border)
- Size: icon circles ≈48–64px diameter; icon itself ≈24–32px
- Source style: geometric and minimal (similar to Phosphor, Lucide, or Streamline Light)
- Never use filled/solid icons, emoji, or illustrated icons
- One icon per concept — never stack or group icons
- Icon circles may use a **subtle inner-shadow or recessed effect** to create depth (e.g., the concave inset at the top of pill-shaped cards)

---

## Connectors and Flow

### Line Semantics
Line style encodes the type of flow or relationship. This must be consistent within and across diagrams:

| Line style | Meaning | Example usage |
|---|---|---|
| **Solid** (1–1.5px) | Primary flow — the main sequence of steps or data path | Pipeline arrows, card-to-card progression |
| **Dashed** (1–1.5px) | Auxiliary or contextual — secondary inputs, optional paths, logical boundaries | Factual verification links, definition box borders, trigger container borders |
| **Dotted border** | Scope or boundary — signals "this is a context zone, not a process step" | Definition boxes, input containers, quadrant labels |

Never use the same line style for two different semantic purposes within one diagram.

### Arrow Rules
- Arrows are **thin (1–1.5px)** with a small, simple triangle arrowhead — not oversized
- Arrow colour: dark gray (`#6B7280`) or black for primary flow; purple (`#4F47E6`) for staged-progression connectors
- **Primary flow arrows** are always **straight and horizontal** — no diagonal lines
- For pipelines: arrows connect the **right edge of one box to the left edge of the next**
- For staged-progressions: arrows sit **between cards**, vertically centred

### Curved Lines (Exception)
Curved arrows or return paths are permitted **only** to represent iteration, feedback loops, or cyclical processes (e.g., looping arrows between PoC and Pilot phases). They must:
- Sit **below or above** the main linear flow — never inline
- Use a consistent curve radius — no freeform bezier paths
- Be clearly distinguishable from the primary straight-arrow flow

Outside of iteration/feedback, never use curved arrows, bezier paths, or diagonal lines.

---

## Card Variants

### Standard Card (Staged Progression, Comparison)
- White or light gray background
- Optional number badge (top-left, inside a small purple circle with white number)
- Icon circle centred at top
- Bold title below icon
- Body text below title
- Optional purple/lavender question/callout box at bottom (light purple fill, rounded corners)

### Gradient Card (Risk/Comparison emphasis)
- Full-height gradient fill (top to bottom)
- White text on dark gradients, black text on light gradients
- Icon circle **protrudes from the top edge** — half inside, half outside the card body, creating a raised/overlapping effect
- Card body has **fully rounded bottom corners** and a **flat or slightly rounded top** that meets the protruding icon circle
- Used only when cards represent **distinct categories at the same level**
- Gradient sequence across a row follows palette order: purple → dark → gray → steel blue

### Pill Card (Numbered Question/Leadership)
- **Stadium/capsule shape** — fully rounded top and bottom ends
- Uniform light gray fill across all cards (no per-card colour variation)
- Top area has a **concave inset** containing the icon circle, creating a recessed/scooped effect
- Large bold number anchored at the bottom of each pill for visual weight
- No connectors between pill cards — they stand independently as a set

### Input/Output Box
- Light gray fill with dotted border for inputs
- Slightly darker or highlighted fill for outputs
- Icon or emoji centred, larger than standard (≈32px)

---

## Definition & Takeaway Zones

Every concept-explainer and most pipeline diagrams include a **bottom section** separated from the main diagram:

- **Left block**: "Definition:" in bold, followed by a 2–3 sentence plain-language explanation. Contained in a dotted-border box with light gray fill.
- **Right block**: Comparison (Without X / With X) or Leader's Insight. Uses bold labels and body text. No container border — just a background fill change or open layout.
- The two blocks sit on the **same horizontal baseline**, separated by whitespace or a thin vertical divider
- This zone is **visually subordinate** to the main diagram — smaller text, lighter treatment

---

## Anti-Patterns (Never Do This)

- Never use coloured backgrounds on the diagram itself — always white
- Never use more than one row of cards (keep everything in a single horizontal band)
- Never use diagonal text or rotated elements
- Never use gradients on text
- Never use thick borders (>2px)
- Never mix icon styles (e.g., some filled, some outlined)
- Never use decorative elements (swirls, blobs, abstract shapes) that don't carry meaning
- Never crowd a diagram — if content doesn't fit in one horizontal row, simplify the message
- Never use a legend or colour key — the layout itself should make relationships obvious
- Never use serif, monospace, or decorative typefaces — all text must be Inter (or Plus Jakarta Sans)
- Never apply purple to borders, large background fills, or full paragraphs of text
- Never duplicate arrows between the same pair of elements — one arrow per logical relationship
- Never draw arrows from individual sub-items when a single arrow from their group container conveys the same relationship