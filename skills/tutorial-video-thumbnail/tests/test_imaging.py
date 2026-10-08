import os
from pathlib import Path
import sys
import unittest

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import imaging


class ImagingTests(unittest.TestCase):
    def test_rotation_and_centering(self):
        source = Image.new("RGBA", (240, 160), "white")
        browser, bounds = imaging.rotated_browser(source, width=300)
        y = imaging.centered_y(bounds, 400)
        self.assertLessEqual(abs((y + bounds[1]) - (400 - y - bounds[3])), 1)
        self.assertTrue(any(0 < value < 255 for value in browser.getchannel("A").tobytes()))

    def test_preserves_source_transparency(self):
        source = Image.new("RGBA", (100, 100), "white")
        ImageDraw.Draw(source).rectangle((35, 35, 65, 65), fill=(0, 0, 0, 0))
        browser, _ = imaging.rotated_browser(source, width=100, angle=0)
        self.assertEqual(browser.getpixel((browser.width // 2, browser.height // 2))[3], 0)

    def test_local_cleanup_only_removes_alpha(self):
        source = Image.new("RGBA", (80, 80))
        draw = ImageDraw.Draw(source)
        draw.rectangle((30, 20, 70, 65), fill="white")
        draw.line((5, 45, 29, 45), fill="white", width=1)
        mask = Image.new("L", source.size, 0)
        ImageDraw.Draw(mask).rectangle((0, 0, 29, 79), fill=255)
        cleaned = imaging.clean_alpha_slivers(source, mask)
        before, after = source.getchannel("A"), cleaned.getchannel("A")
        self.assertIsNone(ImageChops.subtract(after, before).getbbox())
        self.assertIsNotNone(ImageChops.difference(after, before).getbbox())
        self.assertIsNone(ImageChops.difference(after.crop((30, 0, 80, 80)),
                                                before.crop((30, 0, 80, 80))).getbbox())

    def test_shoulder_anchor(self):
        source = Image.new("RGBA", (100, 100))
        ImageDraw.Draw(source).rectangle((0, 80, 99, 99), fill="white")
        y, row = imaging.shoulder_safe_y(source, 900)
        self.assertEqual(row, 80)
        self.assertGreaterEqual(y + row * 9, 1080)

    def test_no_side_clipping(self):
        source = Image.new("RGBA", (100, 100))
        ImageDraw.Draw(source).rectangle((30, 20, 70, 99), fill="white")
        self.assertEqual(imaging.shoulder_safe_y(source, 900), (180, None))

    def test_shadow_opacity(self):
        source = Image.new("RGBA", (10, 10), "white")
        result, origin = imaging.shadowed(source, offset=(20, 0), blur=0, opacity=90)
        self.assertEqual(origin, (0, 0))
        self.assertEqual(result.getpixel((25, 5))[3], 90)
        self.assertEqual(result.getpixel((5, 5))[3], 255)

    def test_title_padding(self):
        candidates = [os.environ.get("THUMBNAIL_TEST_FONT", ""),
                      "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"]
        font = next((path for path in candidates if path and Path(path).is_file()), None)
        if font is None:
            self.skipTest("Set THUMBNAIL_TEST_FONT to a local italic TTF")
        panel = imaging.title_panel("LONG TITLE", font, font_size=36)
        ink = panel.getchannel("R").point(lambda value: 255 if value > 128 else 0)
        bounds = ink.getbbox()
        self.assertIsNotNone(bounds)
        self.assertGreaterEqual(bounds[1], 19)
        self.assertGreaterEqual(panel.height - bounds[3], 19)
        for row in range(panel.height):
            glyph_row = ink.crop((0, row, panel.width, row + 1)).getbbox()
            if glyph_row:
                panel_row = panel.getchannel("A").crop((0, row, panel.width, row + 1))
                panel_bounds = panel_row.point(lambda value: 255 if value > 128 else 0).getbbox()
                self.assertGreaterEqual(glyph_row[0] - panel_bounds[0], 29)
                self.assertGreaterEqual(panel_bounds[2] - glyph_row[2], 29)

    def test_invalid_cleanup_mask(self):
        with self.assertRaises(ValueError):
            imaging.clean_alpha_slivers(Image.new("RGBA", (10, 10)), Image.new("L", (5, 5)))


if __name__ == "__main__":
    unittest.main()