---
name: create-thumbnail
title: Create YouTube Thumbnails
summary: Create reference-driven YouTube thumbnails locally with fast onboarding, reusable Pillow helpers, and visual checks.
description: "Use when creating or refining YouTube thumbnails from keywords, speaker headshots, demo screenshots, or architecture diagrams. Compose locally with Pillow, match supplied references, and preserve editable source. Triggers: create-thumbnail, YouTube thumbnail, video thumbnail, thumbnail design, refine thumbnail. Does not create videos, generate portraits, or publish to YouTube."
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - ask_user_question
prompt: "$create-thumbnail Use BUILD, DATA, APPS with my attached demo screenshot. No headshot; suggest a clean tutorial layout."
language: en
status: Published
author: Chanin Nantasenamat
type: snowflake
id: create-thumbnail
authors: Chanin Nantasenamat
categories: [content-creation, image-processing]
---

# Create Thumbnail

Produce a local 16:9 thumbnail and reproducible editable source. Follow the user's supplied examples and current instructions; use the defaults below when no newer direction overrides them.

## Start here: quick onboarding

For a new thumbnail, start with one short `ask_user_question` call collecting only missing essentials, before asset searches, dependency checks, or rendering. Read the user's message and supplied attachments first. Skip questions already answered; skip onboarding entirely for revisions or a complete brief.

Ask at most these two questions together:

1. **Thumbnail text:** "Which 2-3 keywords or short phrases should appear on the thumbnail? You can also give me the video title and let me suggest them."
2. **Visuals:** "Can you provide a speaker headshot, a demo-project screenshot, or a project architecture diagram? Attach any you have in chat or paste local file paths; one or more is enough, and you can also say 'none'."

Use text inputs so the user can answer directly without navigating menus. Prefill the text question with topic-specific suggestions when the topic is known. Otherwise use an editable invitation, not unrelated example keywords. The form itself does not upload files; attachments are supplied in chat.

Example tool payload when neither essential is known:

```json
{
  "questions": [
    {
      "header": "Text",
      "type": "text",
      "question": "Which 2-3 keywords or short phrases should appear on the thumbnail? Or share the video title and I can suggest them.",
      "defaultValue": "Suggest keywords from my video title: "
    },
    {
      "header": "Visuals",
      "type": "text",
      "question": "Can you provide a speaker headshot, demo screenshot, or architecture diagram? Attach any you have in chat or paste local paths; one or more is enough, or say 'none'.",
      "defaultValue": "I'll attach images, paste local paths, or say none."
    }
  ]
}
```

After the answer, proceed to the first draft without a second approval round. Do not treat unchanged placeholder text as an actual title or file path. If the user promises attachments but none are available yet, pause for those assets rather than searching unrelated personal folders. If the brief still lacks a topic or usable wording, ask only for that missing item.

Accept any combination of visuals; do not require all three. A headshot need not already be transparent. Inspect it before choosing a local cutout approach. Use an architecture diagram in place of the demo screenshot, keeping important labels legible and avoiding browser chrome or tilt when they hurt readability. If the user has no images, make a typography-led draft using the known topic; do not fabricate a speaker or project architecture.

Use the established style and defaults for font, palette, dimensions, layout, and output location. Do not turn these into additional onboarding questions unless the user requests a different style. Do not ask for the speaker's biography, a full script, timestamps, or technical project details merely to start a thumbnail.

## Inputs and defaults

- Required: usable thumbnail wording or a video topic/title from which to suggest it. Collect missing wording and visual availability through quick onboarding above; infer 2-3 short title lines when the user delegates wording.
- Optional: speaker headshot, app/browser screenshot, project architecture diagram, reference directory, background, brand logos, font, output directory, and previous version/source. Missing images do not block a typography-led draft.
- Reference directory: use a user-supplied location or references attached in chat. Do not search unrelated personal folders. Without references, use the default tutorial composition below.
- Default tutorial composition: 1920 x 1080 working canvas; large white uppercase Montserrat Black Italic title on black parallelograms at left; app screenshot at right; optional monochrome portrait in front; vibrant geometric background; branding bottom-left.
- Use a subtle cyan/purple hexagonal background when supplied. Other reference palettes remain valid. A pixel dissolve is optional, not a mandatory style element.
- Default output: a new versioned PNG in the requested directory, otherwise a local project output directory. Preserve earlier versions.

## Workflow

For a new request, complete quick onboarding above first. Then follow these steps; do not repeat the intake for each iteration.

### 1. Inspect the actual starting point

Read the current source/config and latest PNG before editing. A conversation summary may describe changes that never reached disk. Check the configured output filename and actual parameter values.

Use `glob` to locate assets and `read` to view images. For a new style-learning task, inspect a representative sample, state how many were inspected, and distinguish tutorial thumbnails from centered event/showcase designs. For a small revision, inspect the latest image and relevant assets rather than resampling the full library.

Check image dimensions, visible-alpha bounds, screenshot crop, font availability, and whether portrait shoulders terminate at source boundaries. Prefer supplied local assets. Do not include a desktop wallpaper, dock, or surrounding applications when the user asks for the browser only. Prefer a clean replacement screenshot over elaborate segmentation.

Use only assets the user is authorized to use, including permission to feature any supplied speaker portrait. Inspect screenshots for account identifiers, emails, tokens, or private customer data and crop or redact those details in a copy before rendering. Never include private source assets in the skill package or upload them to external services without explicit authorization.

### 2. Define a small, editable composition

Create a project-local Python script or JSON configuration plus renderer. Keep asset paths, title lines, font, positions, scales, screenshot angle, effect seed, and output path explicit. Use an import-safe `main()` and avoid rendering on import. Do not modify the reusable skill files for ordinary thumbnail revisions.

Starting values at 1920 x 1080, not rigid constraints:

- Title: x=70, y=200, font size=100, horizontal/vertical padding=32/20, line gap=16. Fit the longest line rather than assuming all phrases fit.
- Browser: width around 60% of canvas, rotation=-5 degrees, 14 px corner radius, soft offset shadow, partly cropped at right. This is a 2D rotation, not a perspective transform.
- Portrait: center-right, usually 800-900 px tall; adjust based on the actual cutout, face position, title, screenshot content, and shoulder boundaries.
- Branding: baseline region near the bottom-left. For the learned two-brand arrangement, start with first logo height=100, second=76, bottom margin=35, and a thin 2 x 46 px divider. Preserve each logo's aspect ratio and optical balance.

Load `references/rendering-lessons.md` for exact geometry, dissolve recipe, and troubleshooting cases. Use the functions in `scripts/imaging.py` for the repeated low-level operations; read that file before integrating them.

### 3. Compose clean layers

Layer order: background, scattered pixels if requested, screenshot with shadow, portrait, title panels, branding. Preserve source transparency and composite RGBA layers with `alpha_composite`.

**Title:** Match panel slant to the font's actual italic angle. Fit glyph ink in slanted coordinates so all four sides retain black padding. Do not substitute a rectangle for italic text or add text outlines/shadows. Use a real heavy italic font and disclose substitutions.

**Screenshot:** Resize and rotate at 4x resolution with transparent gutter; downsample with Lanczos. Center the visible browser alpha bounds, excluding gutter and shadow. Save those bounds before a dissolve so adding the effect does not shift the screenshot.

**Portrait:** Preserve a useful existing alpha channel. Thresholding dark/light pixels can erase glasses, hair, skin, and clothing. For clipped shoulders, first consider framing or a better source. If the user requests generative repair, check whether an appropriate tool is available. Never describe cropping, scaling, or alpha cleanup as generative fill. Disclose a framing workaround and any unresolved clipping. Do not alter facial identity.

**Branding:** Prefer official supplied reverse/white wordmarks over recoloring raster text. Inspect white transparent logos against a colored background before deciding they are blank. Draw the divider as a rectangle rather than a font glyph. If a multiplication symbol is specifically requested, use `×` in an upright regular font, not italic title text.

### 4. Add or refine effects only when requested

For a lower-left pixel dissolve, follow the bounded, deterministic recipe in `references/rendering-lessons.md`. Use mixed-size nonoverlapping cells, full-cell opacity, a mostly solid browser edge, and sparse particles that shrink and fade outward. Avoid a uniform checkerboard, wire mesh, cloudy patch, or particle clumps.

Multiply the dissolve mask by the original alpha; never introduce opaque pixels outside the original screenshot. Generate the shadow from the final alpha. Protect branding from both particles and blurred shadow.

If a crop shows a stray line, locate it in full-image coordinates before editing. Use narrowly masked alpha cleanup only after confirming the affected corner. Global erosion can damage otherwise smooth browser edges.

### 5. Render, inspect, and verify

Check Python dependencies with `python3 -c "import PIL, fontTools"`. The bundled `pyproject.toml` supports an isolated environment via `uv run --project <ABSOLUTE_SKILL_DIR> python <ABSOLUTE_SCRIPT_PATH>`. No Snowflake connection is needed. Store fonts in a durable asset location with their license/provenance when acquired; do not rely on `/tmp` font paths.

Render to a new versioned output. Open the actual PNG with `read`; also inspect a 320 x 180 preview and close crops of title edges, rotated borders, dissolve, shoulders, and logos. Generating a file is not sufficient verification.

Automated checks should cover dimensions, nonempty output, intended centering, panel padding, alpha-only removal, and shoulder placement when the framing heuristic applies. For scoped edits, compare against the prior version and verify protected regions remain unchanged. Include the shadow's blur extent in allowed-change bounds: a region near branding may contain legitimate shadow changes even when the logo itself is unchanged.

Visual review must still confirm face visibility, title fit, optical balance, mobile legibility, branding spacing, and absence of line slivers. Pixel-difference and alpha assertions do not prove aesthetic quality. Record which checks ran; a failed or syntactically invalid validation command is not a passed test.

Fix and reinspect at most three cycles per requested revision, then report remaining issues. Keep unrelated layout choices unchanged. If delivery requires an upload-size limit, check the current limit and file bytes; retain the PNG master and create an optimized derivative if necessary.

### 6. Deliver

Provide a local link to the new thumbnail and its editable source/config, resolution, and a short description of the change. Mention substitutions or unperformed generative repair. Do not upload, publish, or share externally without explicit authorization.

## Tools and reusable helpers

- `Read`: source inspection and visual review; `Glob`: targeted asset discovery; `Write`/`Edit` (or `apply_patch` where available): manual source/config edits; `Bash`: local Python rendering/tests. Use the equivalent tool names exposed by the current Cortex Code surface.
- `scripts/imaging.py`: `title_panel`, `rotated_browser`, `visible_bounds`, `centered_y`, `shadowed`, `shoulder_safe_y`, and `clean_alpha_slivers`. These are importable helpers, not a full composition CLI or a generative editor.
- Verify helpers with `python3 -m unittest discover -s <ABSOLUTE_SKILL_DIR>/tests -v`. Tests use synthetic images and available local fonts; report font-dependent skips.

## Stopping points

Use `ask_user_question` for the initial missing-essential intake, then only for promised assets that have not arrived, missing context that prevents meaningful work, materially ambiguous wording/style, destructive overwrite, or an external upload/paid service needing authorization. Reuse known preferences and supplied inputs without asking again. Disclose unavailable generative capabilities rather than silently substituting an unrelated operation.

## Output

A versioned thumbnail, editable local composition, and concise verification status. Keep per-video portraits, screenshots, and account-specific details outside this reusable skill.

## Examples

### Quick start

User: `$create-thumbnail I need a thumbnail for a tutorial.`

Expected: one short intake asking for 2-3 keywords or the video title, plus availability of a headshot, demo screenshot, or architecture diagram. Use defaults for other design choices.

### Complete brief

User: `$create-thumbnail Use BUILD, DATA, APPS with my attached demo screenshot. No headshot; suggest a clean tutorial layout.`

Expected: skip intake, inspect the attachment, create a local versioned 1920 x 1080 PNG and editable source, then inspect the rendered output at full and mobile-preview sizes.

### Architecture or no images

User: `$create-thumbnail Use MULTI-TENANT and EMBEDDING with this architecture diagram instead of a screenshot.`

Expected: preserve diagram label readability without forcing browser chrome. If the user instead says no images are available, create a typography-led draft without inventing a person or architecture.

### Scoped revision

User: `Move the headshot up and right and remove the thin line at the dissolve edge.`

Expected: inspect the existing source and latest PNG, adjust only the requested elements, check shoulder clipping and corner alpha, and save the next version. Disclose any unperformed generative repair.