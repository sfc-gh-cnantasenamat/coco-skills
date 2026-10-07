# Troubleshooting and Boundaries

| Symptom | Cause and happy path |
| --- | --- |
| Face-following circle jiggles | Track/review shoulders or use a fixed crop. Do not add increasingly aggressive face-following to fix it. |
| Tracker returns no valid body samples | Detector assumptions may fail for clothing, jacket openings, lighting. Inspect masks; do not copy recording-specific morphology kernels. Fall back to a reviewed fixed center. |
| Different recording uses an old crop | Bind caches/samples to source hashes and review timeline/offset changes. Never trust filename alone. |
| Screen is stretched or clipped | Probe actual aspect ratio and fit within both canvas dimensions. Do not reuse a hard-coded padded-proxy crop. Current proxies contain only their fitted content. |
| Larger screen removes margins | Clarify area versus width/height growth and reject overflowing geometry. |
| Circle is displaced during scaling | Recompute masks at actual overlay dimensions. Old FFmpeg dynamic `geq` chains could retain stale geometry. |
| Background red/blue swapped | OpenCV uses BGR, Pillow uses RGB; convert at the boundary. |
| Equal margins look unequal | Downward shadow extends farther below; check the circle boundary, not shadow extent. |
| Long final renders or wrong screen frame | Use sequential FPS-normalized original decoding, not repeated OpenCV seeking on VFR. |
| Final frame missing | Probe duration plus offsets. Permit only the explicit 0.2-second tail tolerance, never hold missing middle frames indefinitely. |
| Audio offset applied twice | Reuse the approved soundtrack unchanged; offsets apply only when assembling a new soundtrack. |
| Audio clicks or drifts | Segment concat makes hard joins. Listen and prepare a reviewed corrected soundtrack; no automatic fade/drift fix is bundled. |
| Color tags missing after VideoToolbox | The helper adds H.264 VUI via `h264_metadata` and probes all three tags. If still absent, preserve the file, inspect and remux a fresh output with correct metadata only when pixels are known BT.709. |
| Decoder broken pipe | Investigate phase and process exits. Fixed-frame readers now emit exactly the needed number of frames and consume to completion; errors before completion are failures, not harmless warnings. |
| Output already exists | Pick a new revision. Never replace `-n` with `-y` or delete delivered outputs. |
| Incomplete cache | Preserve for diagnosis. Use a new output directory after fixing the cause; do not trust partially written proxies. |
| Tool poll repeats logs | Check the existing background job. Do not start another render from repeated or delayed logs. |
| User cannot locate output | Reveal the specific file in the platform file manager; do not regenerate or upload it. |

## Known scope limits

- Supports local SDR BT.709 square-pixel unrotated media with one relevant video/audio stream; preflight stops on unsupported color/geometry. Normalize separately with review.
- Output canvas is landscape near-16:9; not a portrait/shorts editor.
- Source offsets are nonnegative trims, not a general multi-track timeline. No drift correction or nonlinear editing UI.
- No bundled speech transcription, automatic boundary detection, generalized body detector, or every-frame head-clearance detector.
- Fixed style includes default transition motion and shadow treatment. More styles require explicit implementation and testing, not undocumented config keys.
- Approved soundtrack stream copy requires AAC with edit-matched duration. New audio is encoded once before identity comparisons.
- Full source/cache hashing costs I/O; it prevents accidental stale-cache reuse. Renderer decodes both tracks throughout the configured edit, including full-screen regions.
- Partial failed outputs are intentionally retained and lack a completion record. Never call them delivered.
- H.264 color-tag repair does not tone-map HDR or transform the actual pixel color space.
- Automated verification is necessary but does not replace listening and visual review. Report tested encoders/platforms accurately.