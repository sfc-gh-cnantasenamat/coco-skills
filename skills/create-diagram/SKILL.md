---
name: create-diagram
description: "Create and refine clean architecture, system-flow, and swimlane diagrams as local PNGs using Python/Pillow. Use for architecture diagrams, two-lane diagrams, pipeline diagrams, blog architecture images, and pastel swimlane diagrams with orthogonal connectors. Triggers: create-diagram, draw architecture, architecture PNG, pastel architecture diagram, Pillow diagram, swimlane diagram. Does not require Excalidraw, Graphviz, a browser, or external uploads."
---

# Create Diagram

Create a publication-ready PNG and editable JSON layout using the bundled Pillow renderer. Use a clean, fixed-coordinate layout with pastel swimlanes, rounded nodes, and orthogonal connectors.

## Inputs

- Required: system or process to depict, supplied as a description or readable source files.
- Optional: output directory, filename, reference image, lane titles, palette overrides, font path.
- Defaults: white background, two pastel horizontal lanes when appropriate, 1400 x 1000 logical pixels, 2x PNG export, sans-serif text.
- Infer reasonable defaults from the current project. Ask only about missing architecture facts or genuinely ambiguous scope, using `ask_user_question`.

## Workflow

### 1. Ground the Diagram

Read the relevant code or documentation before drawing. Identify components, runtime boundaries, request/response flow, data sources, and any validation or retry paths. Do not invent infrastructure or imply that query results feed a renderer when it uses separate local data. Distinguish orchestration order from direct component-to-component calls.

Inspect any reference image with `read`. Preserve its visual conventions unless the user asks for a redesign. Do not deploy services or run Snowflake queries merely to illustrate an architecture.

### 2. Write Labels, Then Author the Layout

Write short, connected sentences before placing nodes. Each action should name its actor, connect any function/tool identifier to a verb, and explain the purpose or result. Readers should not need to recognize an API name to understand the flow.

- Prefer "The app sends the request via `request_result()`, which calls the backend" over stacked fragments such as "Application client / request_result / Backend API".
- Prefer "The service calls `validate_result`, a procedure that checks the proposed fields against the data" over an isolated identifier followed by unrelated noun phrases.
- Explain wrapper-to-API relationships explicitly. Use words such as "via", "calls", "using", and "returns"; proximity alone does not express a relationship.
- Keep prose concise, usually one or two sentences per node. Break lines at phrase boundaries. Expand the node or canvas before shrinking the font.
- Use regular Arial for prose and bold Courier New for function, API, and tool identifiers by default. Connecting words such as "via", spaces, and sentence punctuation remain in regular Arial; do not bold the entire sentence. Center mixed-font runs as one line and align them on a shared baseline so punctuation does not float.
- Make the entire lane heading bold Arial, including its separators and explanatory text. Use `Frontend | <technology> | <role>` and `Backend | <technology or orchestrator> | <role>` when those boundaries fit the system. Keep node prose regular and identifiers bold Courier New.
- Use a descriptive overview title when appropriate, such as "Overview of Architecture and Workflow of <system>". Preserve the user's chosen wording and check its width rather than forcing a project-branded title.
- Keep examples generic. Project names describe systems, not visual styles.

Read `assets/two-lane.diagram.json` and `scripts/render_diagram.py` relative to this skill's directory. Use the example as a layout starting point, not as an architectural assumption.

Use `write` to create `<output-dir>/<name>.diagram.json`. For revisions, read and edit the existing layout rather than patching a flattened PNG. Keep the bundled renderer unchanged for normal diagram work.

Layout JSON:

```json
{
  "width": 1400,
  "height": 1000,
  "scale": 2,
  "elements": [
    {"type":"box","id":"input","x":60,"y":180,"width":230,"height":105,"style":"input","text":"User request\nInput form"},
    {"type":"arrow","id":"request","points":[[300,232],[380,232]]}
  ]
}
```

Element types:

- `zone`: rounded background lane with a bold top-left label; requires `x`, `y`, `width`, `height`.
- `box`: rounded node with centered multiline label; same geometry fields.
- `text`: standalone label; requires `x`, `y`, `text`.
- `arrow`: ordered absolute `points`, with an arrowhead at the last point.
- `line`: same point format, without arrowheads; use for legend swatches.

Common options: `bold` (boolean, defaults to true for zone headings and false for other prose), `font_size` (default 22), `color` (text or connector color), `stroke_width` (default 2), `dashed` (connectors), `fill` and `stroke` (box/zone color overrides). Each element needs a unique `id`. Put zones first, then nodes, connectors, and annotations so background fills cannot cover content. Colors are validated by Pillow during rendering.

For mixed-font labels, use `text_lines` instead of `text`. Each line contains runs with `text` and an optional boolean `code` (default false). Setting `code: true` selects bold monospace automatically; no separate bold flag is needed. Line breaks are explicit; do not put newlines inside runs. All runs use the element's `font_size`. Plain `text` remains supported. `text_lines` works on `text` elements too, not only boxes.

Code font (Courier New Bold) is roughly 13% wider per character than regular Arial at the same size (~9.6px vs ~8.5px per character at 16px). When converting existing plain-text labels to `text_lines` with `code: true` runs, the text will be wider. Recalculate whether it fits and widen the box, split to multiple lines, or widen the parent zone/canvas as needed. Do not assume text that fit in regular font will fit in code font at the same width.

```json
{"type":"box","id":"client","x":390,"y":180,"width":330,"height":130,"font_size":20,"style":"process","text_lines":[
  [{"text":"The app sends the request"}],
  [{"text":"via "},{"text":"request_result()","code":true},{"text":"."}],
  [{"text":"The backend returns a result."}]
]}
```

Palette styles:

| Style | Fill | Stroke | Meaning |
|---|---|---|---|
| input | #a5d8ff | #4a9eed | Inputs and query steps |
| process | #d0bfff | #8b5cf6 | Processing and services |
| output | #b2f2bb | #22c55e | Outputs |
| check | #ffd8a8 | #f59e0b | Validation |
| data | #c3fae8 | #06b6d4 | Storage and datasets |
| app | #f0eaff | #c4b5fd | Application lane |
| service | #eaf2ff | #a5c4f5 | Backend lane |

### 3. Apply Layout Rules

- Use a short 28-32px title, 20-22px node labels, and 18-20px annotations. Do not shrink text to solve crowding; enlarge the canvas or split labels over lines. Minimum font size is 16px; the renderer rejects smaller sizes.
- Measure labels using the renderer's font metrics. It rejects labels wider than `width - 32` or taller than `height - 24` for boxes. Two lines of text at 16px need box height >= 65-70px; three lines need >= 85-90px. Always run `--check` before rendering.
- Leave at least 24-40px between nodes and at least 10px between an arrow tip and its destination edge.
- Inner boxes must maintain at least 20-25px margins from their parent zone's edges on all four sides. Do not let inner boxes touch or nearly touch zone borders; this creates a cramped appearance. When zones contain multiple boxes side by side, ensure visible gaps between adjacent boxes (15-20px minimum).
- Zone headings occupy approximately 35px from the zone's top edge. The first contained element must start at least 35px below the zone's top y-coordinate to avoid overlapping the heading text.
- When a box uses a custom `fill` that matches its parent zone's `fill`, the box visually disappears into the zone background. Use a fill shade noticeably lighter or darker than the zone, or omit the custom fill and rely on a built-in style. For example, a box inside a pink zone (`#fce7f3`) should use `#fdf2f8` (lighter pink) rather than the same `#fce7f3`.
- Route bent arrows orthogonally through empty corridors, never through labels or unrelated boxes. Keep lane headings clear.
- Make dashed connectors long enough to show at least three full dashes and two visible gaps before the arrowhead. With the renderer's 8px dash / 8px gap pattern, every dashed segment must be at least 56 logical pixels; prefer 60-80px. For a straight arrow with 10px clearance at both ends, allow at least 76px between boxes. Enlarge the canvas or move nodes instead of compressing the dash pattern, shrinking arrowheads, or changing data arrows to solid. Check short vertical connectors especially, and use the same pattern in the legend.
- Give the final straight segment before every bent arrowhead at least 30px, preferably 40-60px. A 5-10px segment makes the triangle collide with its bend. The renderer rejects this geometry.
- When another actor revises a failed proposal, show an explicit revision node, a feedback arrow (such as "Invalid + reason"), and a return arrow (such as "Recheck, at most one retry"). A validator self-loop wrongly suggests that the validator revises its own input. Use a U-shaped self-loop only when it accurately describes the same component's retry behavior; keep generous terminal segments.
- Verify retry limits and final-failure behavior from source. Do not invent a valid-only submission gate, retry count, or terminal failure branch.
- Put orchestration ownership in the lane heading, such as "The agent calls tools in numbered order". Do not imply that tools call one another when an orchestrator controls them.
- Separate metadata/semantic layers from underlying tables if combining them obscures which component accesses which data.
- Use actual solid and dashed `line` elements in legends, followed by their meanings. Do not write the words "Solid" and "Dashed" as substitutes for samples.
- Keep legends limited to actual visual encodings. Explanatory prose such as "Tool sequence shown inside the agent" belongs in a caption or lane heading if needed.
- Apply legend styles consistently, including local data paths. If dashed lines mean data access, do not use a solid data connector merely because it is inside the app lane.
- Keep fill colors pastel and text dark. Use dark teal (#0e7490) for data access and dark amber (#b45309) for retries. Color is secondary to labels and line styles.
- Check architecture meaning as well as layout: arrows encode an explicit relationship, not simply that two boxes are nearby.
- When converting a diagram to use code font for identifiers (tool names, table names, schema names, etc.), work top-down: widen the canvas first, then widen zones proportionally, then adjust box widths and positions. Do not try to widen individual boxes in isolation — the extra width cascades through the entire layout. A 1400px canvas may need to become 1600px when adding code-font identifiers throughout.

### 4. Render Locally

Use Python 3.10+ with Pillow. Check `python3 -c "import PIL; print(PIL.__version__)"`. If unavailable and `uv` is installed, run via the bundled `pyproject.toml` using `uv run --project <SKILL_DIR> python ...`. Dependency installation may need network access; do not download fonts or upload source data.

Replace `<SKILL_DIR>` with this skill's absolute directory and use absolute input/output paths:

```bash
python3 <SKILL_DIR>/scripts/render_diagram.py /absolute/path/architecture.diagram.json --check
python3 <SKILL_DIR>/scripts/render_diagram.py /absolute/path/architecture.diagram.json --output /absolute/path/architecture.png
```

The renderer prefers local regular Arial for prose and Courier New Bold for code, with regular sans-serif and bold monospace DejaVu/Liberation fallbacks respectively. Use `--font /absolute/path/font.ttf`, `--bold-font /absolute/path/sans-bold.ttf` (defaults to Arial Bold for lane headings), and `--code-font /absolute/path/mono-bold.ttf` to override them. Use an actual bold font file rather than synthetic stroke thickening. If exact Courier New Bold is requested but unavailable, disclose the fallback rather than claiming it was used. Never download fonts automatically. It refuses to overwrite an existing PNG unless `--overwrite` is supplied; review the existing artifact first. Parent output directories must already exist. The editable source is the input `.diagram.json` file; this is not an Excalidraw file.

### 5. Visually Verify

Open the generated PNG with `read`, both at full resolution and at its intended reading size. Inspect every element, not just the most recent edit:

- Can the reader identify the actor, action, and purpose of every node without recognizing its identifier?
- Does each identifier belong grammatically to the surrounding prose? Are identifiers bold monospace while prose words and punctuation remain regular sans-serif, with shared text baselines?
- Are feedback direction, revision ownership, and retry limits explicit?
- Do arrows match the actual data/control paths and the legend, without crossing labels or unrelated boxes?
- Are lane headings bold and clearly labeled by responsibility, with `|` separators? Does the overview title fit?
- Can short dashed connectors still be distinguished from solid ones at the intended reading size, with several dashes visible outside the arrowhead?
- Are all labels readable, unclipped, and comfortably spaced inside their boxes? Are arrowheads clear of bends?

Inspect lane boundaries, whitespace, and legend too. The automated checks validate text fit and connector geometry, but do not detect all connector/box intersections or label collisions.

If something fails, edit the JSON, rerender, and inspect again. Limit to three revision cycles before reporting an unresolved layout issue or asking the user for a choice. For renderer changes, run:

```bash
python3 -m unittest discover -s <SKILL_DIR>/tests -v
```

When a companion blog/document is in scope, insert or preserve its relative PNG reference and a factual caption. Never overwrite unrelated content.

## Stopping Points

Pause if architectural facts are missing, existing files conflict with the requested output, or the user requests external publishing. Do not upload to Excalidraw or any other external service automatically. No cloud access or credentials are needed for rendering.

## Output

Provide links to the local PNG and editable `.diagram.json`, mention the output resolution, and summarize any limitations. Do not claim a runtime/deployment verification occurred when only a diagram was rendered. Keep reusable skill files in the skill directory and project-specific diagram sources beside their PNGs.
