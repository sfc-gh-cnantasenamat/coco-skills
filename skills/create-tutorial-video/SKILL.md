---
name: create-tutorial-video
description: "Convert a Snowflake sfguide (quickstart) into a narrated Remotion tutorial video with TTS, scene-by-scene structure, and frame-accurate A/V sync. Use when asked to create a tutorial video from an sfguide, convert a quickstart to video, or build a narrated walkthrough video. Triggers: create tutorial video, sfguide to video, convert quickstart to video, narrated tutorial video, remotion tutorial, build tutorial video, make a video from sfguide, tutorial video from guide."
metadata:
  author: Chanin Nantasenamat
  version: "1.1"
  type: workflow
  updated: "2026-09"
---

# Create Tutorial Video from sfguide

Convert a Snowflake sfguide into a narrated Remotion tutorial video with TTS, scene-by-scene structure, and frame-accurate A/V sync.

---

## Prerequisites

- Node.js 18+ and npm
- Remotion 4.x (`@remotion/cli`, `@remotion/google-fonts`, `@remotion/transitions`)
- React 19, TypeScript
- `edge-tts` (Python): `pip install edge-tts`
- `ffprobe` (from ffmpeg): needed for measuring audio durations

---

## Setup

Ask the user:

```
To create a tutorial video, I need:
1. Path to the sfguide markdown (or URL to the published quickstart)
2. Where to create the video project (default: ~/Documents/Coco/video-<slug>/)
3. Do you have screenshots/screen recordings already, or should I plan for mocks?
```

**STOP**: Wait for answers before proceeding.

---

## Stage 1: Analyze the sfguide

Read the guide markdown and extract:

1. **Step-by-step structure** -- each numbered step in the guide becomes a candidate scene.
2. **Personas** -- if the guide follows distinct user roles (e.g., one person works in Snowsight, another in terminal), identify them. Each persona gets an accent color from the Snowflake secondary palette.
3. **Visual type per step** -- classify what the viewer should see:
   - `screenshot` -- Snowsight UI, browser-based workflow
   - `terminal` -- CLI commands (git, snow, etc.)
   - `worksheet` -- SQL statements with results
   - `diagram` -- architecture or overview (custom SVG/React)
   - `video-clip` -- screen recording segment
4. **Key callouts** -- specific UI elements, buttons, or outputs that need visual emphasis (circles, highlights).

Output a scene plan table:

```
| # | Scene ID         | Title                          | Visual Type  | Persona | Duration Est |
|---|------------------|--------------------------------|-------------|---------|-------------|
| 1 | 01-Title         | [Video title]                  | custom      | none    | ~18s        |
| 2 | 02-Overview      | [What we'll build]             | diagram     | none    | ~42s        |
| 3 | 03-SetupSecret   | [First setup step]             | worksheet   | none    | ~29s        |
| ...                                                                                          |
| N | NN-Wrapup        | [Closing]                      | custom      | none    | ~50s        |
```

Present this to the user for approval before proceeding.

---

## Stage 2: Write the Script

Write one paragraph per scene. The script should read naturally when spoken aloud by a TTS engine.

### Script structure

1. **Title scene (hook):** 2-4 sentences. State the relatable problem or "what if", promise the outcome. Close with "and we're starting right now" or "let's dive in."
2. **Overview scene:** Explain the approach, introduce personas if any, set expectations. "And if this sounds like fun, keep on watching. So let's dive in."
3. **Content scenes:** Present-tense narration of what's happening on screen. "And so the first thing that we want to do is..." / "And there you go, our [thing] is created."
4. **Wrapup scene:** Recap what was built, mention related features, community sign-off. "If you've found this video helpful please don't forget to give it a like and subscribe... And as always, happy coding!"

### Voice rules

- **Warm and conversational.** Second-person ("you can..."), inclusive first-person plural ("we're going to..."). The viewer is a peer being guided, not lectured.
- **Present-tense.** Narrate actions as they happen on screen: "now we click...", "and there it is".
- **Unhurried pacing.** Give the viewer time to absorb each step. Avoid cramming too much into one sentence.
- **Accessible, low-jargon.** Explain what a thing is before using it. Spell out acronyms on first use.
- **Flowing transitions.** Connect steps with natural bridges: "now that we have X, let's move on to Y". Avoid abrupt jumps between topics.

### TTS pronunciation tips

These spellings produce natural-sounding speech with edge-tts AriaNeural:
- "account admin" (not "ACCOUNTADMIN")
- "github pat" (not "GitHub PAT")
- "streamlit app dot py" (not "app.py")
- "st dot info" (not "st.info")
- "git checkout dash b" (not "git checkout -b")
- "create integration privilege" (not "CREATE INTEGRATION privilege")
- Leave SQL keywords, API names, and URLs as-is.

Save the full script to `out/tutorial-script.txt` with one paragraph per scene, separated by blank lines.

---

## Stage 3: Scaffold the Remotion Project

If no project exists yet, scaffold one:

```bash
npx create-video@latest --template=blank <project-name>
```

Or invoke the `remotion-create` skill.

### Required project layout

```
src/
  Root.tsx           -- registers Tutorial + per-scene compositions
  Tutorial.tsx       -- sequences all scenes with TransitionSeries
  narration.ts       -- AUTO-GENERATED durations (do not hand-edit)
  fonts.ts           -- Inter + JetBrains Mono, Snowflake brand palette, persona colors
  scenes/            -- one file per scene (thin: content + SceneShell)
  components/        -- SceneShell, SceneBg, Voiceover, TalkingHeadZone, BackgroundMusic,
                        Screenshot (ScreenshotSequence), Terminal, Worksheet, VideoClip
public/
  voiceover/         -- narration mp3s (one per scene)
  screenshots/       -- Snowsight screenshots (1280x949, ~4:3)
  videos/            -- screen recording clips (if any)
  music/             -- background music (lofi, low volume)
out/
  tutorial-script.txt
  tutorial.mp4       -- final render
```

### Snowflake brand palette (`fonts.ts`)

```typescript
export const SNOWFLAKE = {
  blue: "#29B5E8",       // Snowflake Blue -- core brand
  midBlue: "#11567F",    // Mid Blue
  midnight: "#000000",   // Midnight -- dark base
  starBlue: "#71D3DC",   // Star Blue
  valencia: "#FF9F36",   // Valencia Orange
  purpleMoon: "#7D44CF", // Purple Moon
  firstLight: "#D45B90", // First Light rose
  windyCity: "#8A999E",  // Windy City neutral
} as const;

export const COLORS = {
  bg: SNOWFLAKE.midnight,
  panel: "#0E1B26",
  panelAlt: "#08131C",
  border: "#1C2C38",
  text: "#FFFFFF",
  textDim: "#C7D2DA",
  textFaint: SNOWFLAKE.windyCity,
  blue: SNOWFLAKE.blue,
  amber: "#FEBC2E",
  green: "#3DDC84",
  coral: "#FF4B4B",
} as const;
```

Persona accent colors: assign from the Snowflake secondary palette (purpleMoon, firstLight, valencia, starBlue). Keep persona colors off-brand so the browser-vs-terminal story stays legible; only shared/default scenes use Snowflake Blue.

### Explanation box styling

Both terminal command captions and screenshot label pills use the same "teacher note" style:

```typescript
export const EXPLAIN = {
  bg: "#E8B84B33",     // amber @ ~20% opacity
  border: "#E8B84B66", // amber @ ~40% opacity
  accent: "#E8B84B",
  text: "#FFFFFF",
} as const;
```

### Tutorial.tsx sequencing

Scenes are sequenced with `TransitionSeries` from `@remotion/transitions`. Alternate transition styles every 3 scenes for visual rhythm:

- `i % 3 === 0` -- fade (linearTiming, 15 frames)
- `i % 3 === 1` -- slide from right (springTiming, damping 200)
- `i % 3 === 2` -- slide from bottom (springTiming, damping 200)

Add a 30-frame intro pause before the first scene (viewers need time to register the video has started).

Total duration: `INTRO_PAUSE + sum(all scene durations) - (numScenes * TRANSITION_OVERLAP)`.

### Root.tsx

Register one `<Composition>` for the full tutorial and one per scene in a `<Folder name="Scenes">` (for rendering individual scene stills during development).

---

## Stage 4: Generate TTS Narration

### Voice and tooling

- Voice: `edge-tts`, voice `en-US-AriaNeural` (free, no API key, deterministic: same text always produces identical audio).
- One mp3 per scene paragraph.

### Generate audio

For each scene paragraph in `out/tutorial-script.txt`:

```bash
python3 -m edge_tts --voice en-US-AriaNeural \
  --text "<paragraph text>" \
  --write-media public/voiceover/NN-scene-name.mp3
```

### Measure durations and build narration.ts

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 public/voiceover/NN-scene-name.mp3
```

For each clip, compute:
```
audioFrames = round(audioSeconds * FPS)
durationInFrames = audioFrames + HEAD + TAIL
```

Where `FPS = 30`, `HEAD = 10` (VOICEOVER_DELAY before audio starts), `TAIL = 45` (breathing room after audio ends).

Generate `src/narration.ts`:

```typescript
// AUTO-GENERATED from measured narration audio (edge-tts en-US-AriaNeural).
// durationInFrames = round(audio*30) + head(10) + tail(45).
export const FPS = 30;

export const NARRATION = {
  title: { src: "voiceover/00-title.mp3", audioFrames: 503, durationInFrames: 558 },
  overview: { src: "voiceover/01-overview.mp3", audioFrames: 1262, durationInFrames: 1317 },
  // ... one entry per scene
} as const;

export const VOICEOVER_DELAY = 10;
```

**CRITICAL**: If narration text changes, you must regenerate the mp3, re-measure the duration, and update narration.ts. These three artifacts MUST stay in sync -- they drift silently otherwise.

---

## Stage 5: Build Scene Components

### SceneShell (the standard scene wrapper)

Every content scene uses SceneShell, which provides:
- **Title band** (top-left): persona kicker pill + scene title
- **Main visual** (left-center): the screenshot/terminal/worksheet/diagram
- **KEY POINTS panel** (right): square bullet (`■`) summary points, accent-colored
- **Voiceover**: the narration audio
- **TalkingHeadZone**: reserved bottom area (for potential talking-head overlay or subtitles)

Props: `persona`, `title`, `points[]`, `pointFrames[]`, `voiceover`, `contentScale`, `children`.

### Visual components

#### ScreenshotSequence (browser UI scenes)

For Snowsight/browser workflow steps:
- Screenshots are 1280x949 placed in a mock browser chrome (URL bar, rounded corners, glow shadow).
- Body sized `FRAME_W=1084 x BODY_H=804` with `objectFit: cover` (edge-to-edge, no side margins).
- `Shot = { src, label?, circle?, at? }`:
  - `at` = absolute scene frame the shot becomes visible. **If any shot sets `at`, the whole sequence uses explicit windows.**
  - `circle = { x, y, rx, ry, rotate?, at? }` in normalized 0..1 body coords. Renders as a wobbly hand-drawn SVG marker stroke in `circleColor` (default pink `#FF4D6D`).
  - `label` = bottom-right explanation pill (moved from top-right to avoid occluding circles).

#### Terminal (CLI scenes)

For git/snow/shell command sequences:
- Walks through commands one at a time: type command, show explanation caption, reveal output, advance.
- `steps: { cmd, out?, explain, at? }[]`
- `startFrame`: delay the first command until it's spoken (idle `$` prompt shows during intro).
- `accent`: persona color for the active command highlight.
- **Pin each command to its narration mention via `step.at`** (absolute scene frame). Without `at`, legacy even-split is used (avoid this).

#### Worksheet (SQL scenes)

For SQL statement sequences:
- Snowsight-style SQL worksheet: reveals lines progressively, then a result strip.
- `sql: string[]` (one entry per line, `""` for blank separators).
- `result?`, `resultFrame?`, `lineFrames?: number[]`.
- Pin SQL lines to narration via `lineFrames`. Give continuation lines the anchor frame + a few frames each so the block reveals together.

#### VideoClip (screen recording scenes)

For pre-recorded screen captures:
- Source recordings are typically 60fps at 2880x1864 (or 1440x932).
- `startFrom`, `endAt` in source video frame space.
- `playbackRate = sourceClipDuration / sceneCompDuration` maps the segment to the scene length.
- `cropTopPx` hides source-video pixels from the top (e.g., macOS title bar).

---

## Stage 6: A/V Sync

**THIS IS THE SINGLE BIGGEST QUALITY LEVER.**

### The core principle

**Whatever is on screen should appear/highlight at the moment the narrator says it -- not before, not after.** Do not distribute screenshots or circles evenly across a scene; pin them to the narration.

### How to time something to a verbal mention

Narration audio starts at scene frame `VOICEOVER_DELAY` (10). An element mentioned at audio-time `T` seconds should appear at:

```
frame = round(T * 30) + 10
```

To find `T` for a phrase, synthesize the narration **prefix up to that phrase** and measure it (edge-tts pacing of a leading substring matches its pacing in the full line, within ~0.5 seconds):

```bash
python3 -m edge_tts --voice en-US-AriaNeural \
  --text "<exact narration text up to the target word>" \
  --write-media /tmp/p.mp3
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/p.mp3
# frame = round(duration * 30) + 10
```

### Convention offsets (account for animation lead-in)

| Element | Offset from mention frame | Reason |
|---------|--------------------------|--------|
| Image swap (`shot.at`) | mention frame **minus ~12** | crossfade `hold` is ~18 frames; image is on screen as the word lands |
| Circle draw (`circle.at`) | mention frame **minus ~6** | ~20-frame draw finishes just after the word |
| Terminal command (`step.at`) | mention frame exactly | command starts typing as it's spoken |
| Worksheet line (`lineFrames[i]`) | mention frame exactly | line fades in as it's mentioned |

### Key sync rules

- Every `shot.at`, `circle.at`, `step.at`, and `lineFrames` value must be derived from a measured narration prefix -- never guessed or evenly distributed.
- Group a SQL statement's continuation lines a few frames after its first line (e.g., `[389, 389, 531, 536, 541, 546]`).
- Set `resultFrame` to the frame the result/confirmation is verbally referenced.
- Re-verify timing after any narration text change (even small edits shift pacing).

---

## Stage 7: Validate and Render

### Type and lint checks

```bash
npx tsc --noEmit        # must pass
npx eslint src           # must pass
```

### Spot-check scene stills

Before a full render, verify timing by rendering individual scene stills at key frames:

```bash
npx remotion still <SceneId> /tmp/check.png --frame=<mention_frame>
```

Check that the expected element (screenshot, circle, command, SQL line) is visible at that frame.

### Full render

```bash
npx remotion render Tutorial out/tutorial.mp4
```

This takes 3-5 minutes. **Run in the background** -- full renders can exceed tool timeout limits:

```bash
npx remotion render Tutorial out/tutorial.mp4 &
```

### Post-render verification

Extract frames at scene boundaries and key moments:

```bash
ffmpeg -ss <time_seconds> -i out/tutorial.mp4 -frames:v 1 /tmp/scene-check.png -y
```

---

## Stage 8: Export and Deliver

1. Final mp4: `out/tutorial.mp4`
2. Script: `out/tutorial-script.txt`
3. Offer to save to Snowflake workspace: `cortex ws cp out/tutorial.mp4 DB.SCHEMA.WS:/videos/`

---

## Lessons Learned / Gotchas

These are hard-won lessons from iterative development. Read before starting.

### A/V sync
- **Even time-splitting of screenshots always desyncs from narration.** Always pin `at` to measured mention frames. This is the #1 quality issue.
- The circled/highlighted region must appear when the narrator mentions it, not before. Audit every highlight against its verbal cue.
- Scenes that transition abruptly: add a short delay (15-30 frames) after spoken words before firing the transition. Without this, the viewer misses the last visual.
- When using pre-recorded human audio instead of TTS, segment the audio file precisely per scene and sync each segment to the millisecond. Do not rely on rough cuts.
- If pacing feels too fast on first review, increase scene durations by ~50% across the board. Viewers need breathing room between ideas.

### Highlights and callouts
- **Prefer translucent highlight boxes over hand-drawn SVG circles.** Circles looked messy and were hard to position accurately. A translucent colored rectangle with a solid border, slowly animated to fade in over the target region, reads cleaner and is easier to maintain.
- Highlight box border should be a solid accent color; fill should be the same color at ~15-20% opacity.
- Position highlights precisely over the UI element they reference. Audit by rendering a still at the mention frame and visually confirming the highlight covers the right region -- off-by-50px is noticeable.
- Persona accent colors for highlights: use Snowflake secondary palette (e.g., `#7D44CF` for one persona, `#D45B90` for another). Keep persona colors distinct from Snowflake Blue so the story stays legible.

### Layout and sizing
- `objectFit: contain` on a 16:9 frame causes side letterboxing. Match the body aspect to the screenshot aspect ratio and use `cover`.
- The label pill at top-right can occlude highlights near the top of screenshots. Place it at bottom-right, or below the screenshot aligned left.
- The URL bar in mock browser chrome is single-line (`whiteSpace: nowrap`, maxWidth 940). Keep URLs short enough not to ellipsize.
- Text in mock browser screenshots must fit on a single line. If it wraps to a new line, shorten the text or widen the container.
- Mock SQL worksheets should closely match the actual Snowsight worksheet appearance (toolbar, run button, result grid styling). Generic code-editor mocks look cheap.
- Do NOT apply zoom-in animations to screenshots. Static entry (fade or slide) looks more professional. Zoom creates a "PowerPoint 2003" feel.

### Scene structure
- The **overview must be its own scene**, not a text overlay that stalls on the title card. Viewers expect visual progression after the title.
- Each scene needs a clear title at the top and a summary caption/key-points panel to the side. The visual alone is not enough -- viewers skim.
- Explanation boxes (command captions, label pills) should use a consistent style: accent-colored background at ~20% opacity, matching solid border, white text. The amber style (`#E8B84B`) works well as a default; for persona scenes, match the persona accent color instead.

### React 19
- `React.FC` does NOT include `children` in React 19. Declare `children: React.ReactNode` explicitly in every component that accepts children.

### Narration consistency
- `out/tutorial-script.txt`, the mp3 files, and `narration.ts` MUST stay mutually consistent. They drift silently.
- Narration and any on-screen captions must be the same content -- do not maintain two separate scripts. When the user asks to "combine the script with the caption", they mean the narration text IS the caption text.
- The exported script text file should contain ONLY the spoken words -- no scene headers like "SCENE 1 / 8 — TITLE", no stage directions, no formatting. Just the paragraphs the narrator reads.
- After editing narration text: regenerate the mp3, re-measure duration, update narration.ts, re-verify all `at` frames in that scene.

### Rendering
- Full renders can exceed a 20-minute foreground tool timeout. Run them in the background and poll the log.
- Prefer rendering a single scene still at the mention frame to check sync before committing to a full render.
- Scene composition IDs follow the pattern `01-Title`, `02-Overview`, etc. (see Root.tsx).

### Video start
- Add a ~1-second pause (30 frames) at the start of the video. This is intentional: viewers who click play need time for the video to load and cache; without it they miss the first word. Do not remove this even if it looks like "dead air."

### Decorative elements
- **Avoid animated decorative elements** (particle dots, diagonal lines, floating shapes) that compete with content. These were consistently flagged as distracting in every review.
- Background radial gradient: use a subtle center glow with a large radius. Avoid harsh vignettes.
- Background music should be very quiet (10-15% volume). Use lofi/ambient that doesn't compete with narration. Reuse existing music from `~/Documents/Coco/` library if available (e.g., `B02-Machine-Learning-Lullaby-edited.wav`).
- Avoid unnecessary UI chrome on scenes: fork icons, extra toolbars, or decorative borders that aren't in the actual product. Every element should either be from the real UI or directly serve the narration.

### Audit checklist
After building, audit the video from a developer/user POV:
- [ ] Does the hook make the value proposition clear in the first 5 seconds?
- [ ] Is every on-screen element synced to its verbal mention (not before, not after)?
- [ ] Are transitions smooth -- no abrupt cuts mid-sentence, with breathing room after each point?
- [ ] Is the pacing comfortable (not too fast)? If in doubt, add 50% more time.
- [ ] Are all highlight regions positioned precisely over their target UI elements?
- [ ] Is the mock browser / worksheet visually close to the real Snowsight UI?
- [ ] Does the wrapup mention related features and include a CTA?
- [ ] Is the exported script file clean -- spoken words only, no headers or formatting?
- [ ] Are narration text, mp3 files, narration.ts durations, and on-screen captions all in sync?
- [ ] Does the 1-second opening pause exist?
