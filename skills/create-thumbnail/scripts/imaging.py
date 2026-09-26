"""Import-safe local composition helpers; no asset downloads or file writes."""

import math

from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def title_panel(text, font_path, font_size=100, padding_x=32, padding_y=20, supersample=4):
    """Return padded white glyphs on a font-angle-matched black parallelogram."""
    if not text.strip() or min(font_size, padding_x, padding_y, supersample) <= 0:
        raise ValueError("Provide nonempty text and positive size, padding, and scale")
    font = ImageFont.truetype(str(font_path), font_size * supersample)
    bounds = font.getbbox(text)
    ink = Image.new("L", (bounds[2] - bounds[0], bounds[3] - bounds[1]), 0)
    ImageDraw.Draw(ink).text((-bounds[0], -bounds[1]), text, font=font, fill=255)
    ink = ink.crop(ink.getbbox())
    with TTFont(font_path) as metadata:
        slope = math.tan(math.radians(-metadata["post"].italicAngle))
    projected = []
    for row in range(ink.height):
        row_bounds = ink.crop((0, row, ink.width, row + 1)).getbbox()
        if row_bounds:
            projected.append((row_bounds[0] + slope * row, row_bounds[2] + slope * row))
    left = min(pair[0] for pair in projected)
    right = max(pair[1] for pair in projected)
    inset_x, inset_y = padding_x * supersample, padding_y * supersample
    height = ink.height + 2 * inset_y
    shear = slope * height
    width = right - left + 2 * inset_x
    shift = -min(0, shear)
    panel = Image.new("RGBA", (math.ceil(width + abs(shear)) + 1, height), (0, 0, 0, 0))
    ImageDraw.Draw(panel).polygon(
        [(shift + shear, 0), (shift + width + shear, 0),
         (shift + width, height - 1), (shift, height - 1)], fill="black"
    )
    ink_x = round(shift + shear + inset_x - left - slope * inset_y)
    panel.paste((255, 255, 255, 255), (ink_x, inset_y), ink)
    return panel.resize(
        (math.ceil(panel.width / supersample), math.ceil(panel.height / supersample)),
        Image.Resampling.LANCZOS,
    )


def visible_bounds(image, threshold=128):
    bounds = image.convert("RGBA").getchannel("A").point(
        lambda alpha: 255 if alpha >= threshold else 0
    ).getbbox()
    if bounds is None:
        raise ValueError("Image has no visible pixels at the requested threshold")
    return bounds


def rotated_browser(image, width=1152, angle=-5, radius=14, supersample=4, gutter=4):
    """Return smooth RGBA browser and its pre-effect visible bounds."""
    if width <= 0 or supersample < 1 or radius < 0 or gutter < 1:
        raise ValueError("Invalid browser dimensions or supersampling parameters")
    image = image.convert("RGBA")
    height = max(1, round(image.height * width / image.width))
    browser = image.resize((width * supersample, height * supersample), Image.Resampling.LANCZOS)
    corners = Image.new("L", browser.size, 0)
    ImageDraw.Draw(corners).rounded_rectangle(
        (0, 0, browser.width - 1, browser.height - 1), radius=radius * supersample, fill=255
    )
    browser.putalpha(ImageChops.multiply(browser.getchannel("A"), corners))
    pad = gutter * supersample
    padded = Image.new("RGBA", (browser.width + 2 * pad, browser.height + 2 * pad))
    padded.alpha_composite(browser, (pad, pad))
    rotated = padded.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    rotated = rotated.resize(
        (round(rotated.width / supersample), round(rotated.height / supersample)),
        Image.Resampling.LANCZOS,
    )
    return rotated, visible_bounds(rotated)


def centered_y(bounds, canvas_height=1080, shadow_pad=0):
    return round((canvas_height - (bounds[3] - bounds[1])) / 2) - bounds[1] - shadow_pad


def shadowed(image, offset=(12, 12), blur=22, opacity=90):
    """Return shadowed layer and original-image origin within that layer."""
    if blur < 0 or not 0 <= opacity <= 255:
        raise ValueError("Invalid shadow blur or opacity")
    image = image.convert("RGBA")
    pad = math.ceil(blur * 3)
    origin = (pad + max(0, -offset[0]), pad + max(0, -offset[1]))
    size = (image.width + 2 * pad + abs(offset[0]), image.height + 2 * pad + abs(offset[1]))
    mask = Image.new("L", size, 0)
    mask.paste(image.getchannel("A").point(lambda alpha: round(alpha * opacity / 255)),
               (origin[0] + offset[0], origin[1] + offset[1]))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)))
    layer.alpha_composite(image, origin)
    return layer, origin


def shoulder_safe_y(image, target_height, canvas_height=1080, threshold=16, margin=3):
    """Return (y, first_side_row); only use on a verified transparent shoulder cutout."""
    if target_height <= 0:
        raise ValueError("Portrait height must be positive")
    alpha = image.convert("RGBA").getchannel("A")
    rows = [row for row in range(image.height)
            if max(alpha.getpixel((0, row)), alpha.getpixel((image.width - 1, row))) > threshold]
    first = min(rows) if rows else None
    if first is None:
        return canvas_height - target_height, None
    return canvas_height - int(first * target_height / image.height) + margin, first


def clean_alpha_slivers(image, region_mask, kernel=5):
    """Remove narrow alpha features only within a caller-selected L mask."""
    if region_mask.mode != "L" or region_mask.size != image.size:
        raise ValueError("Cleanup mask must be L mode and match the image size")
    if kernel < 3 or kernel % 2 != 1:
        raise ValueError("Cleanup kernel must be an odd integer >= 3")
    result = image.convert("RGBA")
    alpha = result.getchannel("A")
    opened = alpha.filter(ImageFilter.MinFilter(kernel)).filter(ImageFilter.MaxFilter(kernel))
    reduced = ImageChops.darker(alpha, opened)
    result.putalpha(Image.composite(reduced, alpha, region_mask))
    return result