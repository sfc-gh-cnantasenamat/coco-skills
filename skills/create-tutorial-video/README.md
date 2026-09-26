# create-tutorial-video

> Convert a Snowflake sfguide (quickstart) into a narrated Remotion tutorial video with TTS, scene-by-scene structure, and frame-accurate A/V sync.

## What it does

The skill reads an sfguide markdown, extracts a step-by-step scene plan, writes a conversational narration script, scaffolds a Remotion project, generates TTS audio with edge-tts, and pins every visual element to its verbal mention for frame-accurate A/V sync. The result is a polished tutorial video with Snowflake brand styling, mock browser/worksheet components, and smooth transitions.

## Usage

Invoke with `$create-tutorial-video` or let Cortex Code activate it automatically when you say something like:

```
Create a tutorial video from this sfguide.
Convert this quickstart to a narrated video.
Build a tutorial video from my guide markdown.
```

## Workflow stages

| Stage | What happens |
|---|---|
| 1. Analyze | Extract scenes, personas, visual types from the sfguide |
| 2. Script | Write conversational narration (TTS-friendly pronunciation) |
| 3. Scaffold | Create Remotion project with brand palette and components |
| 4. TTS | Generate per-scene mp3s with edge-tts AriaNeural |
| 5. Build | Implement scene components (Screenshot, Terminal, Worksheet, VideoClip) |
| 6. A/V Sync | Pin every visual to its measured narration mention frame |
| 7. Render | Type-check, spot-check stills, full mp4 render |
| 8. Deliver | Export mp4 and clean script |

## Requirements

- Node.js 18+ with Remotion 4.x
- Python 3 with `edge-tts` (`pip install edge-tts`)
- `ffprobe` (from ffmpeg) for measuring audio durations

## Author

Chanin Nantasenamat

## License

Apache 2.0 — see [LICENSE](LICENSE).
