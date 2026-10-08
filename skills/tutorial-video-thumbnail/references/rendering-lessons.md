# Rendering lessons from iterative thumbnail work

These recipes capture the transferable fixes, not an instruction to reproduce one video's exact layout. Coordinates below use a 1920 x 1080 canvas; scale effect sizes when changing resolution.

## Slanted title panels

Montserrat Black Italic had an angle near -11.3 degrees in the inspected font. Read `post.italicAngle` with FontTools instead of baking that angle into all fonts.

At 4x resolution, render a cropped glyph-ink mask. Set `slope = tan(radians(-italic_angle))`. For every nonempty row, project its left and right ink bounds using `u = x + slope*y`. Let `u_min` and `u_max` enclose all rows. With padding `px, py` in supersampled pixels:

```text
panel_height = ink_height + 2*py
shear = slope*panel_height
panel_width = u_max - u_min + 2*px
polygon = [(shear,0), (panel_width+shear,0),
           (panel_width,panel_height), (0,panel_height)]
ink_x = shear + px - u_min - slope*py
ink_y = py
```

Normalize polygon x-coordinates if the shear is negative. Downsample once after drawing. Measuring only the font's ordinary rectangular bounding box misses italic overhangs. Refit or rephrase a long title; do not let the panel disappear under the portrait or off canvas.

## Smooth browser rotation and centering

Use 4x resize, rounded alpha mask, a transparent gutter of at least 4 output pixels on all sides, expanded bicubic rotation, and Lanczos downsampling. Rounded mask endpoints are `(width-1, height-1)`. Multiply rounded alpha by existing image alpha rather than replacing useful source transparency.

Compute bounds with alpha threshold around 128 before the dissolve. If those local bounds are `(left, top, right, bottom)`, the browser layer y is:

```text
y = round((canvas_height - (bottom-top))/2) - top
```

Subtract the shadow padding when positioning a layer that includes the shadow. Check top and bottom margins differ by at most one pixel when fully in frame. Do not assert one session's measured margins as universal.

Create shadow alpha by multiplying the final screenshot alpha by the desired shadow opacity, blur, then alpha-composite the actual screenshot. Transparency and shadow opacity are separate quantities.

## Portrait shoulders and honest editing

Examine the original RGBA cutout before using background removal. Good transparency avoids destructive brightness thresholds and unnecessary large model downloads.

For a cutout whose only source-side clipping is at its shoulders, find the first row where alpha on either outermost column exceeds 16. With resized scale `s`, place at:

```text
y = canvas_height - floor(first_clipped_row*s) + 3
```

This puts the clipped source sides below canvas. Enlarging while retaining that anchor moves the head up, but can crop hair or push the face into the title, so inspect visually. If the portrait is opaque edge-to-edge, has unrelated side clipping, or has useful complete shoulders, do not apply this heuristic blindly. Use ordinary composition or a better cutout.

Scaling does not reconstruct missing shoulders. Only claim generative repair after an actual generative edit. If generation needs external upload, obtain explicit authorization for those assets first.

## Optional lower-left dissolve

1. Save pre-effect browser bounds and original alpha. Use a local `random.Random(seed)` (27 was used during development) to make revisions comparable.
2. Tile output-space in 16 px blocks. Keep about 35% whole; subdivide the rest into four 8 px cells. Cells must not overlap or leave gutters.
3. Inverse-map cell centers into the unrotated screenshot. For Pillow rotation `-5 degrees`, use `theta=+5 degrees` and centered coordinates:

```text
source_x = cos(theta)*relative_x + sin(theta)*relative_y + source_width/2
source_y = -sin(theta)*relative_x + cos(theta)*relative_y + source_height/2
bottom_distance = source_height-source_y
```

4. Restrict to an ellipse at the lower-left with radii roughly 195 x 165 px. Set `r = hypot(max(0,source_x)/195, max(0,bottom_distance)/165)`; skip `r>=1`. Clip to screenshot/cell limits too.
5. Perturb the contour slightly: `0.045*sin(source_x/23 + bottom_distance/31)`. Normalize `(r+contour-0.18)/0.68` to [0,1], then smoothstep `t*t*(3-2*t)`. Add bounded noise proportional to `(1-t)` so the solid edge stays solid. Snap retention below 0.25 to zero and above 0.80 to one.
6. Paint the entire cell with its opacity, ending at `x+size-1, y+size-1`. Inset cells produced an unwanted wire-mesh artifact. Apply `multiply(original_alpha, mask)`.
7. Emit particles from some faded cells, sampling screenshot RGB only where original alpha is substantial. Example: `travel=random()**1.5`, `drift=22+205*travel`, size `max(2, round(11*(1-0.8*travel)))`, opacity `round(230*(1-travel)**1.25)`.
8. Drift left and curve upward: `particle_y = cell_y - 0.18*drift - 0.0018*drift**2 + jitter`. Keep particles separated by approximately their half-sizes plus 7 px. Keep them sparse; no individual particle shadows.
9. Exclude expanded logo/title bounding boxes, not merely the bottom of the canvas. The earlier y=925 cutoff protected most branding but was only a layout-specific approximation.
10. Build the browser shadow after dissolve and any cleanup, so a solid shadow does not reveal the removed corner. Inspect on the actual background.

## Removing thin residual lines

Rotated antialiasing intersecting square cell cuts can leave tiny line slivers. Inspect a crop to locate the artifact. `clean_alpha_slivers` performs grayscale morphological opening (`MinFilter(5)` then `MaxFilter(5)`), limits the result using `darker(original, opened)`, and selects it only inside an explicitly supplied local mask.

It can only remove alpha, but may also remove narrow desirable features. Do not apply globally, to the face, or before locating the offending region. Use a conservative mask slightly beyond the dissolve region and leave the rest of the browser identical. Regenerate the shadow after cleanup.

## Troubleshooting checklist

| Symptom | Fix |
| --- | --- |
| Desktop border remains | Crop accurately or request/use the app-only screenshot |
| Italic text almost touches black edge | Fit projected ink bounds, including all four padding margins |
| Jagged tilted edge | Supersample, add gutter, downsample, and use correct alpha composition |
| Browser appears off-center | Center visible pre-dissolve alpha, not the shadow's rectangle |
| Face/shirt holes | Restore original alpha; avoid color-threshold segmentation |
| White logo looks empty | Preview over dark/color background and inspect nonzero alpha |
| Heavy/italic separator | Draw a thin rectangle; typography should not control its thickness |
| Dissolve is wire mesh | Remove insets; vary full-cell opacity instead |
| Dissolve is cloudy/checkerboard-like | Tighten transition, mix cell sizes, preserve solid edge |
| Tiny line after pixelation | Inspect and apply corner-local alpha-only opening |
| Unchanged-region test fails near logos | Examine diff bounds; include legitimate shadow blur, then retest |
| Handoff says newer version than disk | Read actual script/output and resume from verified state |
| Works only during original session | Replace temporary font dependencies with durable supplied assets |

## Evaluation prompts

Test future skill changes against these cases:

- Bare "create a thumbnail": first asks for 2-3 keywords/title and availability of a headshot, screenshot, or architecture diagram in one short form, without starting filesystem exploration.
- Complete brief with wording and attachments: skips onboarding and starts inspection; a revision never repeats intake.
- Title supplied, no images available: offers sensible keyword suggestions in the intake and proceeds with a typography-led draft after the user says none; does not demand a portrait or invent architecture.
- Architecture diagram only: accepts it as the main visual and preserves label readability rather than forcing screenshot/browser styling.
- New video title plus screenshot/portrait/background: outputs a readable versioned 16:9 thumbnail and editable source, no private assets copied into the skill.
- "Make the italic title boxes match the slant": black margins survive on every side, including a long line.
- "Enlarge and center the browser": smooth borders, visible top/bottom margins matched, title and branding unchanged unless necessary.
- "Refine the pixel dissolve": deterministic sparse mixed-size pixels; no grid gaps, line slivers, solid old shadow, or branding collision.
- "Move the face up/right; fill shoulders if needed": checks original clipping, preserves identity, distinguishes framing from generation.
- "Continue from the previous version": verifies files instead of treating a prose handoff as authoritative.