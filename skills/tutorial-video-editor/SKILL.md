---
name: tutorial-video-editor
title: Tutorial Video Editor
summary: Combine camera and screencast recordings into local tutorial videos with presenter overlays, animated transitions, and proxy-first editing.
description: "Combine existing talking-head and screencast recordings into a local tutorial video with a circular presenter, animated intro/outro transitions, backgrounds, and shadows. Use for presenter overlays, picture-in-picture tutorials, combining camera and screen recordings, stable presenter cropping, proxy edits, or final rendering of these compositions. Triggers: tutorial video editor, edit tutorial video, compose tutorial video, combine talking head and screencast, circle presenter, camera overlay, screencast composition. Not for generating narrated videos from written guides or creating slides."
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - ask_user_question
prompt: "Combine my talking-head and clean screencast recordings into a tutorial with a circular presenter and animated transitions. Start with a 720p preview."
language: en
status: Published
author: Chanin Nantasenamat
type: snowflake
id: tutorial-video-editor
authors: Chanin Nantasenamat
categories: [content-creation, developer-tools]
---

# Tutorial Video Editor

## Workflow

Create a local, configuration-driven edit from existing recordings. Use **720p previews and a full-screen screencast by default**, optional 480p for faster rough edits, and original recordings for final output. No media uploads, Snowflake operations, external transcription, or third-party APIs.

### 1. Inspect and collect only missing choices

Read any project `AGENTS.md` and [references/workflow.md](references/workflow.md). Reuse decisions already made in the conversation.

Identify camera video, clean screen video, audio sources, output folder, and desired intro/tutorial/outro. Probe media, verify shared timing, and inspect representative images. Never use screen picture containing a baked-in presenter when a clean screen exists.

For narration-based boundaries, review an existing transcript or use an available local transcription tool after checking its installation. Propose frame-aligned boundaries from the narration; the bundled scripts do not perform transcription or infer boundaries. Ask only when source alignment, boundaries, or soundtrack selection materially changes the edit. Use the question tool for questions.

### 2. Prepare project configuration

Create a project-owned JSON file based on [assets/project.example.json](assets/project.example.json), not inside this skill directory. Read [references/configuration.md](references/configuration.md) for field semantics. Choose a fresh output revision.

- Use rational FPS and integer frame boundaries.
- Default to a reviewed, fixed body/shoulder-centered crop. Do not follow the face frame by frame.
- Fit the entire screen proportionally with `screen_inset: 0` and `corner_radius: 0`. A matching 16:9 source fills the canvas edge-to-edge, without a decorative border or rounded screen corners. Preserve other aspect ratios with letterboxing rather than cropping or stretching. Keep the circular presenter and its black shadow with equal right/bottom margins; keep full-screen camera intro/outro and their transitions.
- Preserve explicit settings in existing projects unless the user requests a change. The inset-card style remains available through nonzero `screen_inset` and `corner_radius`.
- Use the project's chosen background image or a two-color gradient. Asset generation does not authorize applying an unrelated background.
- `proxy_height: 720` defaults to 1280 x 720 for readable screen text. Optional `480` gives 854 x 480 with square pixels, a close even-width approximation to 16:9. Geometry scales from canvas height; final output is not an upscale of the proxy.
- Set `audio.mode: approved` to stream-copy an existing approved AAC soundtrack. Otherwise use `segments` to create one soundtrack from camera intro/outro and tutorial audio, then reuse it across revisions.
- Never inherit offsets, dimensions, tracking values, or timings from a different recording.

### 3. Preflight and proxy

Prerequisites: Python 3.11+, FFmpeg/FFprobe on PATH with H.264 encoding, NumPy, OpenCV, Pillow. Use an existing compatible Python environment or `uv run --project <SKILL_DIR> python ...` with the bundled `pyproject.toml`. Do not replace a working environment unnecessarily. The scripts discover tools on PATH and never call a shell with media paths.

In these commands, `SKILL` is the absolute directory containing this file, `CONFIG` is the absolute project JSON, and `PYTHON` is the selected interpreter. Run long jobs in the tool's background mode and poll the same job.

```bash
"$PYTHON" "$SKILL/scripts/tutorial_video.py" preflight --config "$CONFIG"
"$PYTHON" "$SKILL/scripts/tutorial_video.py" prepare --config "$CONFIG"
"$PYTHON" "$SKILL/scripts/tutorial_video.py" render --config "$CONFIG"
"$PYTHON" "$SKILL/scripts/tutorial_video.py" verify --render-dir "$RENDER_DIR"
```

Preflight is read-only and reports source hashes and geometry. `prepare` creates fingerprinted proxies and a soundtrack if needed. `render` also prepares missing derivatives automatically. The default output directory is `<output_dir>/<revision>-proxy-720p/` (or 480p when requested); `video.mp4` and `render.json` live there.

Inspect the generated contact sheet, full-resolution tutorial still, both moving transitions, and audio at both joins. Review head clearance at leaning/turning moments. Verification reports mark visual review as required; tests do not certify all-frame head visibility or perceptual synchronization.

### 4. Iterate

Modify only requested properties. Use a new revision for each export. The shared proxy/audio cache avoids regenerating unchanged inputs. If increasing size by a percentage, distinguish area from dimensions; area scales dimensions by `sqrt(factor)`. Reject overflow rather than hiding it with cropping.

The helper renders complete edits, not disjoint transition-only reels. For a fast representative test, create a separate short configuration with corresponding source offsets and valid boundaries; keep it distinct from the full project configuration.

### 5. Final render after explicit approval

Pause unless the user has explicitly authorized a final render of this revision. Praise of a proxy alone is not authorization. Record the approved proxy path and do not rerender it.

```bash
"$PYTHON" "$SKILL/scripts/tutorial_video.py" render --config "$CONFIG" --final --final-approved
"$PYTHON" "$SKILL/scripts/tutorial_video.py" verify --render-dir "$FINAL_DIR" --approved-proxy "$APPROVED_PROXY"
```

The flag records an operator decision, not an access-control boundary. Never supply it without conversational authorization. Full renders decode originals sequentially with FPS normalization, not OpenCV seeks per output frame. Finite decoder outputs avoid padded-tail broken pipes. H.264 VUI color tags are written during encoding and probed before a render is marked complete.

### 6. Deliver

Read the verification report and inspect visual evidence. State resolution, duration, unchanged/prepared soundtrack status, and any remaining limitation. Reveal the actual file with the platform file manager (macOS `open -R`). Keep project sources, caches, previous outputs, and reports local and intact.

## Stopping Points

- Ambiguous source alignment, unreviewed color space, missing audio, or unsuitable crop: explain the specific blocker and ask for the missing decision.
- Proxy rendered and checked: wait for layout feedback or final-render approval.
- Existing output or incomplete cache: preserve it. Use a new revision/output directory after investigating; do not silently delete or overwrite.
- Repeated failure: after two informed repair attempts, stop and report logs and remaining cause instead of launching duplicate jobs.

## Tools and References

- `scripts/tutorial_video.py`: `preflight`, `prepare`, `render`, `verify` commands above.
- [references/configuration.md](references/configuration.md): exact settings, offsets, tracking, supported inputs.
- [references/troubleshooting.md](references/troubleshooting.md): fixes and known limitations.
- `tests/test_video.py`: unit tests and opt-in synthetic integration tests. Run with `python -m unittest discover -s <SKILL_DIR>/tests`; set `TUTORIAL_VIDEO_INTEGRATION=1` to run media tests. Tests create temporary synthetic media only.

## Outputs

Project JSON, fingerprinted proxies, optional assembled soundtrack, versioned proxy/final MP4, render provenance, unique verification reports and contact sheets. Keep approval state and pending visual checks in project notes, not global memory. No private media or project-specific source paths belong in the installed skill.