# Editing Workflow

## Before rendering

Inspect real source metadata. A 2160-pixel-high screen recording need not be 3840 pixels wide or have the camera's frame rate. Keep its whole picture proportional. A clean screen source may have no audio; identify the separate audio-bearing recording explicitly.

Establish whether sources share a timeline. Correlate common audio at the beginning, middle, and end when available; verify against recognizable actions and lip sync. A constant offset fixes constant lag, not clock drift. Never reuse the previous project's measured offset. If source alignment needs negative offsets or drift correction, create a reviewed normalized derivative first.

Use local transcript/narration to identify where introduction becomes demonstration and where closing remarks begin. Translate proposed times into integer frames. The agent chooses/explains boundaries; the scripts accept configuration rather than claiming speech understanding.

## Framing

Sample camera frames during turns, leans, and the beginning/end. Choose the shoulder/body midpoint and ensure the head fits the circular crop. Favor a fixed center over noisy face tracking. A dark-shirt silhouette detector worked for one session but is not a universal body detector. If using a detector, validate coverage, explicitly handle missed detections, smooth/dead-zone motion, and review sampled head clearance. Elliptical head envelopes are more useful than rectangular empty corners for circle clearance.

The desired introduction and outro are full-screen camera; tutorial is a full-screen screencast plus circular presenter. Default to zero screen inset and square screen corners. Fit proportionally, filling the canvas for matching aspect ratios and letterboxing other ratios without cropping content. The camera circle is independent of the screen so it can move without duplicating a baked-in presenter. Equal right/bottom margins refer to the canvas, not the screen rectangle or the extent of a blurred shadow.

## Iteration and approval

720p is the default preview resolution so screen text is easier to review. Use 480p only when requested for a faster rough edit. Preserve explicit existing project settings unless a change is requested. Maintain original recordings and reusable proxies separately. Scale geometry and animation offsets from canvas height. Increasing area 10% requires multiplying both dimensions by sqrt(1.10), then checking fit. Never silently crop on overflow.

Preview the scene and transitions, check audio boundaries, and explain any limitation before approval. Approval applies to the named revision. A different revision needs its own final authorization. The script flag is an additional mistake-prevention mechanism, not proof of consent.

## Final checks

Render originals through the same FPS-normalized composition as the proxy. Do not upscale a proxy or repeatedly seek a VFR original by nominal frame index. Confirm BT.709 conversion and metadata separately. Decode the entire output and compare the whole soundtrack to its approved/prepared reference.

Review contact sheet, a full-size screen still, both transitions in motion, and final frame. Numerical image differences can miss local flaws; sampled head checks do not cover every frame. State that distinction honestly. Reveal the actual output file locally, and keep the reports so future sessions do not need to repeat successful work.