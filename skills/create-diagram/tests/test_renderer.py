import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location("render_diagram", ROOT / "scripts/render_diagram.py")
renderer = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(renderer)


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((ROOT / "assets/two-lane.diagram.json").read_text())

    def test_example_renders(self):
        image = renderer.render(self.layout)
        self.assertEqual(image.size, (2800, 2000))
        self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_short_final_bent_segment_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "request")
        item["points"][-3] = [40, 565]
        item["points"][-2] = [235, 565]
        with self.assertRaisesRegex(ValueError, "final arrow segment"):
            renderer.validate(self.layout)

    def test_label_overflow_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "input")
        item["text"] = "A label that is much too long for the available box width"
        with self.assertRaisesRegex(ValueError, "label does not fit"):
            renderer.validate(self.layout)

    def test_duplicate_id_rejected(self):
        self.layout["elements"].append(copy.deepcopy(self.layout["elements"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate element"):
            renderer.validate(self.layout)

    def test_outside_canvas_rejected(self):
        self.layout["elements"][0]["x"] = 1399
        with self.assertRaisesRegex(ValueError, "outside the canvas"):
            renderer.validate(self.layout)

    def test_diagonal_bend_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "request")
        item["points"][1][0] += 5
        with self.assertRaisesRegex(ValueError, "orthogonal"):
            renderer.validate(self.layout)

    def test_zero_length_segment_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "retry")
        item["points"].insert(1, item["points"][0])
        with self.assertRaisesRegex(ValueError, "zero-length"):
            renderer.validate(self.layout)

    def test_height_overflow_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "input")
        item["text"] = "one\ntwo\nthree\nfour\nfive"
        with self.assertRaisesRegex(ValueError, "label does not fit"):
            renderer.validate(self.layout)

    def test_legend_has_real_solid_and_dashed_lines(self):
        image = renderer.render(self.layout)
        self.assertEqual(image.getpixel((410 * 2, 956 * 2)), (30, 30, 30))
        self.assertEqual(image.getpixel((773 * 2, 956 * 2)), (14, 116, 144))
        self.assertEqual(image.getpixel((782 * 2, 956 * 2)), (255, 255, 255))

    def test_mixed_fonts_keep_prose_and_punctuation_separate(self):
        item = {"id": "mixed", "font_size": 20, "text_lines": [[
            {"text": "via "}, {"text": "request_result()", "code": True}, {"text": "."},
        ]]}
        rows, width, height = renderer.layout_text(item, 2)
        runs = rows[0]["runs"]
        self.assertEqual(runs[0][1].getname(), runs[2][1].getname())
        self.assertNotEqual(runs[0][1].getname(), runs[1][1].getname())
        self.assertAlmostEqual(width, sum(font.getlength(content) / 2 for content, font, _ in runs))
        self.assertGreater(height, 0)
        self.assertGreater(rows[0]["baseline"], 0)
        self.assertLess(rows[0]["baseline"], height)

    def test_code_defaults_to_bold_without_bolding_prose(self):
        item = {"id": "weights", "text_lines": [[
            {"text": "via "}, {"text": "request_result()", "code": True}, {"text": "."},
        ]]}
        rows, _, _ = renderer.layout_text(item, 2)
        runs = rows[0]["runs"]
        self.assertIn("bold", runs[1][1].getname()[1].lower())
        for position in (0, 2):
            self.assertNotIn("bold", runs[position][1].getname()[1].lower())

    def test_mixed_runs_draw_on_shared_baseline(self):
        from unittest.mock import patch
        item = {"type": "box", "id": "mixed", "x": 20, "y": 20,
                "width": 350, "height": 80, "font_size": 20, "text_lines": [[
                    {"text": "via "}, {"text": "request_result()", "code": True}, {"text": "."},
                ]]}
        spec = {"width": 400, "height": 120, "elements": [item]}
        with patch.object(renderer.ImageDraw.ImageDraw, "text", autospec=True) as draw_text:
            renderer.render(spec)
        self.assertEqual(draw_text.call_count, 3)
        baselines = [call.args[1][1] for call in draw_text.call_args_list]
        self.assertEqual(len(set(baselines)), 1)
        self.assertTrue(all(call.kwargs["anchor"] == "ls" for call in draw_text.call_args_list))

    def test_mixed_label_overflow_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "client")
        item["text_lines"][0].append({"text": "very_long_function_name()" * 5, "code": True})
        with self.assertRaisesRegex(ValueError, "label does not fit"):
            renderer.validate(self.layout)

    def test_mixed_label_height_overflow_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "client")
        item["text_lines"] *= 4
        with self.assertRaisesRegex(ValueError, "label does not fit"):
            renderer.validate(self.layout)

    def test_ambiguous_text_formats_rejected(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "client")
        item["text"] = "Conflicting label"
        with self.assertRaisesRegex(ValueError, "not both"):
            renderer.validate(self.layout)

    def test_invalid_runs_rejected(self):
        invalid_lines = [[], [[]], [[{"text": "two\nlines"}]], [[{"text": "via", "code": "false"}]]]
        for lines in invalid_lines:
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                renderer.layout_text({"id": "invalid", "text_lines": lines}, 2)

    def test_missing_code_font_reports_override(self):
        with self.assertRaisesRegex(ValueError, "--code-font"):
            renderer.load_font(20, ROOT / "missing-font.ttf", code=True)

    def test_plain_text_still_supported(self):
        rows, _, _ = renderer.layout_text({"id": "plain", "text": "First line\nSecond line"}, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["runs"][0][0], "First line")

    def test_lane_headings_default_to_bold(self):
        item = next(item for item in self.layout["elements"] if item["id"] == "app_zone")
        rows, _, _ = renderer.layout_text(item, 2)
        self.assertIn("bold", rows[0]["runs"][0][1].getname()[1].lower())
        item["bold"] = False
        rows, _, _ = renderer.layout_text(item, 2)
        self.assertNotIn("bold", rows[0]["runs"][0][1].getname()[1].lower())

    def test_standalone_bold_heading(self):
        rows, _, _ = renderer.layout_text({"id": "heading", "text": "Frontend", "bold": True}, 2)
        self.assertIn("bold", rows[0]["runs"][0][1].getname()[1].lower())

    def test_invalid_bold_flag_rejected(self):
        with self.assertRaisesRegex(ValueError, "bold must be boolean"):
            renderer.layout_text({"id": "heading", "text": "Frontend", "bold": "true"}, 2)

    def test_missing_bold_font_reports_override(self):
        with self.assertRaisesRegex(ValueError, "--bold-font"):
            renderer.load_font(20, ROOT / "missing-font.ttf", bold=True)

    def test_short_dashed_segments_rejected(self):
        for points in ([[50, 100], [50, 65]], [[50, 100], [120, 100], [120, 65]]):
            spec = {"width": 200, "height": 200, "elements": [
                {"id": "short", "type": "arrow", "dashed": True, "points": points},
            ]}
            with self.subTest(points=points), self.assertRaisesRegex(ValueError, "dashed segments"):
                renderer.validate(spec)

    def test_minimum_dashed_arrow_has_three_visible_dashes(self):
        for scale in (1, 2):
            spec = {"width": 150, "height": 150, "scale": scale, "elements": [
                {"id": "dashed", "type": "arrow", "dashed": True,
                 "points": [[50, 110], [50, 54]]},
            ]}
            image = renderer.render(spec)
            for offset in (4, 20, 36):
                self.assertEqual(image.getpixel((50 * scale, (110 - offset) * scale)), (30, 30, 30))
            for offset in (12, 28):
                self.assertEqual(image.getpixel((50 * scale, (110 - offset) * scale)), (255, 255, 255))

    def test_skill_registration(self):
        registry = json.loads((ROOT.parent.parent / "skills.json").read_text())
        self.assertEqual(registry["paths"].count(str(ROOT)), 1)


if __name__ == "__main__":
    unittest.main()
