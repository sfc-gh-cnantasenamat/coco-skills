# create-diagram

> Create clean architecture, system-flow, and swimlane diagrams as local PNGs using Python and Pillow.

## What it does

The skill takes a JSON diagram specification and renders it to a PNG using a bundled Python renderer. It supports boxes, zones (grouped regions), connectors with labels, text annotations, and a legend. Mixed fonts (regular + monospace) are supported via `text_lines` with `{"text": "...", "code": true}` runs. A built-in validator checks that all labels fit within their boxes before rendering.

## Usage

Invoke with `$create-diagram` or let Cortex Code activate it automatically when you say something like:

```
Draw an architecture diagram for my pipeline.
Create a two-lane swimlane diagram.
Make a system diagram showing the data flow.
```

## Key features

- **JSON-based specification** — declarative layout with boxes, zones, connectors, text, and legend
- **Mixed fonts** — combine regular and monospace text in the same label via `text_lines`
- **Fit validation** — `--check` mode rejects diagrams where labels overflow their boxes
- **2x rendering** — default scale factor produces crisp PNGs at double resolution
- **Pastel color palette** — built-in styles (process, input, output, decision, zone) with orthogonal connectors

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Full specification and layout rules |
| `scripts/render_diagram.py` | Python renderer (Pillow-based) |
| `tests/test_renderer.py` | Unit tests for the renderer |
| `assets/two-lane.diagram.json` | Example two-lane diagram spec |
| `assets/two-lane.png` | Rendered example output |
| `pyproject.toml` | Python dependencies (Pillow) |

## Requirements

- Python 3.10+ with Pillow installed (`pip install pillow`).
- No browser, Graphviz, or external services required.

## Author

Chanin Nantasenamat

## License

Apache 2.0 — see [LICENSE](LICENSE).
