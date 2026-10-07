# Configuration Reference

Paths resolve against the JSON file, not the current working directory. Use local files only. Unknown top-level/style/audio keys are rejected to catch typos. The example contains illustrative boundaries and filenames; replace them before use.

## Required fields

| Field | Meaning |
| --- | --- |
| `version` | Schema version, currently 1 |
| `camera`, `screen` | Original picture files, exactly one video stream each |
| `frames` | Total output frames, positive integer |
| `tutorial_start` | First tutorial frame; preceding transition ends one frame earlier |
| `outro_start` | First expansion frame and switch back to camera audio |
| `output_dir` | Local directory for cache and revision folders |
| `revision` | Alphanumeric/underscore/hyphen name such as `v2` |
| `audio` | Approved soundtrack or segment inputs below |

## Optional fields and defaults

- `fps`: `"24000/1001"`. Preserve exact rational values, not rounded 23.98.
- `transition_frames`: 30, minimum 2. Require `transition <= tutorial_start < outro_start` and `outro_start + transition <= frames`.
- `proxy_height`: 720 by default; 480 is available for rough edits. Output width is nearest even 16:9 width.
- `final_height`: 2160; supported 720, 1080, 1440, 2160.
- `encoder`: `libx264` by default; optionally `h264_videotoolbox` on macOS. Software encoding uses CRF 23 proxy / 18 final, veryfast preset; VideoToolbox requests 3M / 45M. Report actual metadata rather than promising the requested bitrate.
- `camera_offset_seconds`, `screen_offset_seconds`: 0. Nonnegative source trim offsets. **Source time = output time + offset** after normalizing the source start timestamp. Negative offsets are intentionally unsupported: normalize delayed sources in a separate reviewed derivative first.
- `assume_bt709_for_untagged`: false. Set true only after reviewing untagged SDR footage. Explicit non-BT.709, HDR, rotation, or non-square pixels require separate normalization. Do not relabel HDR as SDR.
- `center_samples`: optional path described below.

Frames are `[0, frames)`. Camera remains full-screen before `tutorial_start-transition_frames` and from `outro_start+transition_frames` onward. Audio switches at `tutorial_start` and `outro_start`, independently of the visual morph.

## Audio

Reuse an approved soundtrack:

```json
{"mode": "approved", "path": "approved-edit.mp4"}
```

It must have exactly one AAC audio stream and duration within 0.1 seconds of the edit. MP4/M4A inputs are suitable. The entire track is copied without trimming/re-encoding; the verifier compares decoded PCM hashes. Do not apply synchronization offsets again.

Or assemble once from recordings:

```json
{
  "mode": "segments",
  "camera": "camera.mp4",
  "tutorial": "screen-with-audio.mp4",
  "camera_offset_seconds": 0,
  "tutorial_offset_seconds": 0
}
```

Audio offsets use the same source-time convention, but are independent of video offsets. Camera audio supplies `[0, tutorial_start)` and `[outro_start, frames)`; tutorial audio supplies the middle. Trim, reset timestamps, resample to 48 kHz stereo, concatenate, encode AAC once, then cache the result. There are no automatic fades, normalization, silence padding, or drift correction. Listen to the joins; if clicks or drift need correction, prepare and approve a soundtrack separately and switch to approved mode. Hash equality is against the prepared AAC, not against each pre-encode source.

## Style

Size values are fractions of output canvas height except `presenter_corner_radius`, which is a fraction of presenter side length. Positions are centered for the screen and bottom-right for the presenter.

- `screen_inset`: 0. Fit the entire screen within the canvas without decorative margins. Matching 16:9 sources fill the 720p/final canvas edge-to-edge; other aspect ratios retain letterboxing without crop or stretch. Nonzero values opt into an inset card with minimum clearance on every side. Content dimensions are even for H.264, with at most small rounding/aspect error.
- `corner_radius`: 0, so the screen has square corners. For an inset card, optionally use 12/720; clamped to half the content's smaller dimension.
- `presenter_diameter`: 192/720. Also the side length for a rounded-square presenter.
- `presenter_margin`: 36/720. Same clearance from presenter bounds to bottom and right canvas edges, excluding shadow.
- `presenter_corner_radius`: 0.5 (circle). Range 0 to 0.5; use 0.25 for a heavily rounded square. The mask, shadow, and intro/outro morph share this radius.
- `body_center_x`: 0.5. Normalized horizontal center **after camera cover crop into the output canvas**, not raw sensor coordinates. Center must allow a square height-sized presenter crop; out-of-range centers are clamped by the compositor, so inspect actual framing.
- `background_colors`: two hex RGB values, default cyan/purple. BGR conversion is internal.
- `background_image`: optional local PNG/JPEG, overrides gradient. Center-covered to canvas; no private assets are bundled.

Camera cover-crop, circular mask, no glow, black shadows (0.48 strength, 7/720 downward offset, 9/720 Gaussian sigma), and eased curved transition motion match the session's visual approach. Tiny proxy/final rounding differences are expected. A 480p crop should not be trusted for fine-text judgment; use 720p or a final still.

## Reviewed center samples

Use fixed body-centered framing unless body movement makes it unsuitable. The bundled renderer does not run an automatic face/body detector. Optional pre-reviewed center samples have this format:

```json
{
  "camera_sha256": "full-source-sha256-from-preflight",
  "samples": [[0, 0.53], [60, 0.53]]
}
```

Times are output seconds after camera offset, must increase, and must span the whole output timeline. Centers use the same post-cover coordinate system as `body_center_x`. Fingerprinting prevents use with a different camera file; if offsets/crop/timeline change, review/recreate samples even when the file hash matches. Interpolation does not stabilize noisy samples: smooth/dead-zone them before use and inspect the motion. No automatic head-clearance guarantee is made.

## Caches and provenance

Cache keys include full source SHA-256, offsets, FPS, frame count, relevant geometry, and encoder recipe. Full hashing is deliberate and may take time. Completed cache files have checksums; changed or incomplete cache entries stop reuse. No cache is deleted automatically.

Each output has a new directory and a `render.json` containing resolved configuration, source metadata/hashes, geometry, and soundtrack/video hashes. Verification reads that record, not the latest mutable config. Reports get fresh timestamp/UUID directories, allowing safe repeated checks without overwriting prior evidence.