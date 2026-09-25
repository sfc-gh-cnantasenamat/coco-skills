import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    "input": ("#a5d8ff", "#4a9eed"),
    "process": ("#d0bfff", "#8b5cf6"),
    "output": ("#b2f2bb", "#22c55e"),
    "check": ("#ffd8a8", "#f59e0b"),
    "data": ("#c3fae8", "#06b6d4"),
    "app": ("#f0eaff", "#c4b5fd"),
    "service": ("#eaf2ff", "#a5c4f5"),
}
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "DejaVuSans.ttf",
)


BOLD_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
)

CODE_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    "C:/Windows/Fonts/courbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
    "DejaVuSansMono-Bold.ttf",
)


def load_font(size, font_path=None, code=False, bold=False):
    defaults = CODE_FONT_CANDIDATES if code else BOLD_FONT_CANDIDATES if bold else FONT_CANDIDATES
    candidates = (font_path,) if font_path else defaults
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    flag = "--code-font" if code else "--bold-font" if bold else "--font"
    raise ValueError(f"No TrueType font found. Supply {flag} /absolute/path/font.ttf.")


def positive_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return value


def inside_canvas(xpos, ypos, width, height, identifier):
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (xpos, ypos)):
        raise ValueError(f"{identifier}: coordinates must be finite numbers")
    if not (0 <= xpos <= width and 0 <= ypos <= height):
        raise ValueError(f"{identifier}: point ({xpos}, {ypos}) is outside the canvas")


def layout_text(item, scale, font_path=None, code_font_path=None, bold_font_path=None):
    size = positive_number(item.get("font_size", 22), f"{item['id']}.font_size")
    if size < 16:
        raise ValueError(f"{item['id']}: use at least 16px text; enlarge the layout instead")
    if "text_lines" in item:
        if "text" in item:
            raise ValueError(f"{item['id']}: use text or text_lines, not both")
        lines = item["text_lines"]
        if not isinstance(lines, list) or not lines:
            raise ValueError(f"{item['id']}: text_lines must be a nonempty list")
    else:
        content = item.get("text", "")
        if not isinstance(content, str):
            raise ValueError(f"{item['id']}: text must be a string")
        lines = [[{"text": line}] for line in content.split("\n")]
    bold = item.get("bold", item.get("type") == "zone")
    if not isinstance(bold, bool):
        raise ValueError(f"{item['id']}: bold must be boolean")
    rows = []
    for line in lines:
        if not isinstance(line, list) or not line:
            raise ValueError(f"{item['id']}: each text_lines line must contain runs")
        runs = []
        for run in line:
            if not isinstance(run, dict) or not isinstance(run.get("text"), str) or "\n" in run["text"]:
                raise ValueError(f"{item['id']}: runs require single-line text")
            code = run.get("code", False)
            if not isinstance(code, bool):
                raise ValueError(f"{item['id']}: run code must be boolean")
            selected_font = code_font_path if code else bold_font_path if bold else font_path
            font = load_font(round(size * scale), selected_font, code=code, bold=bold)
            runs.append((run["text"], font, font.getlength(run["text"]) / scale))
        ascent = max(font.getmetrics()[0] for _, font, _ in runs) / scale
        descent = max(font.getmetrics()[1] for _, font, _ in runs) / scale
        row_height = max(size * 1.25, ascent + descent)
        baseline = (row_height - ascent - descent) / 2 + ascent
        rows.append({"runs": runs, "width": sum(run[2] for run in runs),
                     "height": row_height, "baseline": baseline})
    return rows, max(row["width"] for row in rows), sum(row["height"] for row in rows)


def validate(spec, font_path=None, code_font_path=None, bold_font_path=None):
    width = positive_number(spec["width"], "width")
    height = positive_number(spec["height"], "height")
    scale = spec.get("scale", 2)
    if type(scale) is not int or not 1 <= scale <= 4:
        raise ValueError("scale must be an integer from 1 to 4")
    if width * height * scale * scale > 40_000_000:
        raise ValueError("Canvas exceeds 40 million output pixels; reduce dimensions or scale")
    seen = set()
    for item in spec["elements"]:
        identifier = item["id"]
        if identifier in seen:
            raise ValueError(f"Duplicate element id: {identifier}")
        seen.add(identifier)
        kind = item["type"]
        if kind not in ("zone", "box", "text", "arrow", "line"):
            raise ValueError(f"{identifier}: unsupported type {kind}")
        if item.get("style", "input") not in PALETTE:
            raise ValueError(f"{identifier}: unknown palette style")
        if item.get("stroke_width", 2) <= 0:
            raise ValueError(f"{identifier}: stroke_width must be positive")
        if kind in ("line", "arrow"):
            points = item["points"]
            if len(points) < 2:
                raise ValueError(f"{identifier}: at least two points required")
            for point in points:
                inside_canvas(*point, width, height, identifier)
            for start, end in zip(points, points[1:]):
                if math.dist(start, end) == 0:
                    raise ValueError(f"{identifier}: zero-length segment")
                if len(points) > 2 and start[0] != end[0] and start[1] != end[1]:
                    raise ValueError(f"{identifier}: bent connectors must be orthogonal")
                if item.get("dashed", False) and math.dist(start, end) < 56:
                    raise ValueError(f"{identifier}: dashed segments must be at least 56px; increase node spacing")
            if kind == "arrow":
                minimum = 30 if len(points) > 2 else 18
                if math.dist(points[-2], points[-1]) < minimum:
                    raise ValueError(f"{identifier}: final arrow segment must be at least {minimum}px")
                tip_x, tip_y = points[-1]
                if not (12 <= tip_x <= width - 12 and 12 <= tip_y <= height - 12):
                    raise ValueError(f"{identifier}: arrowhead needs 12px canvas margin")
            continue
        xpos, ypos = item["x"], item["y"]
        inside_canvas(xpos, ypos, width, height, identifier)
        if kind in ("zone", "box"):
            box_width = positive_number(item["width"], f"{identifier}.width")
            box_height = positive_number(item["height"], f"{identifier}.height")
            inside_canvas(xpos + box_width, ypos + box_height, width, height, identifier)
        _, text_width, text_height = layout_text(item, scale, font_path, code_font_path, bold_font_path)
        if kind in ("zone", "box"):
            if text_width > item["width"] - 32 or text_height > item["height"] - 24:
                raise ValueError(f"{identifier}: label does not fit; widen the box or insert a newline")
        else:
            inside_canvas(xpos + text_width, ypos + text_height, width, height, identifier)
    return width, height, scale


def draw_segment(draw, start, end, color, stroke_width, dashed, scale):
    distance = math.dist(start, end)
    if not dashed:
        draw.line([start, end], fill=color, width=stroke_width)
        return
    for offset in range(0, math.ceil(distance), 16 * scale):
        first_fraction = offset / distance
        last_fraction = min(offset + 8 * scale, distance) / distance
        first = tuple(start[axis] + (end[axis] - start[axis]) * first_fraction for axis in (0, 1))
        last = tuple(start[axis] + (end[axis] - start[axis]) * last_fraction for axis in (0, 1))
        draw.line([first, last], fill=color, width=stroke_width)


def render(spec, font_path=None, code_font_path=None, bold_font_path=None):
    width, height, scale = validate(spec, font_path, code_font_path, bold_font_path)
    image = Image.new("RGB", (round(width * scale), round(height * scale)), "white")
    draw = ImageDraw.Draw(image)
    for item in spec["elements"]:
        kind = item["type"]
        stroke_width = max(1, round(item.get("stroke_width", 2) * scale))
        if kind in ("line", "arrow"):
            color = item.get("color", "#1e1e1e")
            points = [(xpos * scale, ypos * scale) for xpos, ypos in item["points"]]
            for first, last in zip(points, points[1:]):
                draw_segment(draw, first, last, color, stroke_width, item.get("dashed", False), scale)
            if kind == "arrow":
                prior, tip = points[-2:]
                angle = math.atan2(tip[1] - prior[1], tip[0] - prior[0])
                wing_a = (tip[0] - 11 * scale * math.cos(angle - 0.45), tip[1] - 11 * scale * math.sin(angle - 0.45))
                wing_b = (tip[0] - 11 * scale * math.cos(angle + 0.45), tip[1] - 11 * scale * math.sin(angle + 0.45))
                draw.polygon([tip, wing_a, wing_b], fill=color)
            continue
        xpos, ypos = item["x"] * scale, item["y"] * scale
        rows, text_width, text_height = layout_text(item, scale, font_path, code_font_path, bold_font_path)
        text_color = item.get("color", "#1e1e1e")
        if kind in ("zone", "box"):
            fill, stroke = PALETTE[item.get("style", "input")]
            box_width, box_height = item["width"] * scale, item["height"] * scale
            draw.rounded_rectangle(
                (xpos, ypos, xpos + box_width, ypos + box_height), radius=18 * scale,
                fill=item.get("fill", fill), outline=item.get("stroke", stroke), width=stroke_width,
            )
            if kind == "zone":
                xpos += 20 * scale
                ypos += 16 * scale
            else:
                ypos += (box_height - text_height * scale) / 2
        for row in rows:
            line_x = xpos
            if kind == "box":
                line_x += (item["width"] - row["width"]) * scale / 2
            baseline = ypos + row["baseline"] * scale
            for content, font, run_width in row["runs"]:
                draw.text((line_x, baseline), content, fill=text_color, font=font, anchor="ls")
                line_x += run_width * scale
            ypos += row["height"] * scale
    return image


def main():
    parser = argparse.ArgumentParser(description="Render a local architecture-diagram JSON layout with Pillow.")
    parser.add_argument("spec", type=Path, help="Input .diagram.json layout")
    parser.add_argument("--output", type=Path, help="PNG destination; defaults beside layout")
    parser.add_argument("--font", type=Path, help="Prose TrueType font override")
    parser.add_argument("--code-font", type=Path, help="Code TrueType font override (prefers Courier New Bold)")
    parser.add_argument("--bold-font", type=Path, help="Bold prose font override (prefers Arial Bold)")
    parser.add_argument("--check", action="store_true", help="Validate without writing an image")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing PNG")
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text())
        width, height, scale = validate(spec, args.font, args.code_font, args.bold_font)
        if args.check:
            print(f"Valid: {len(spec['elements'])} elements, {width} x {height}, scale {scale}")
            return
        output = args.output or args.spec.with_suffix(".png")
        if output.suffix.lower() != ".png":
            raise ValueError("Output must have a .png extension")
        if not output.parent.is_dir():
            raise ValueError(f"Output directory does not exist: {output.parent}")
        if output.exists() and not args.overwrite:
            raise ValueError(f"Output exists: {output}; use --overwrite after reviewing it")
        image = render(spec, args.font, args.code_font, args.bold_font)
        image.save(output, format="PNG", optimize=True)
        print(f"PNG: {output.resolve()} ({image.width} x {image.height})")
        print(f"Editable layout: {args.spec.resolve()}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Diagram error: {error}\n")


if __name__ == "__main__":
    main()
