"""Exercise local CLI artifact generation without inference or network calls."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import attach_resources
import local_generate
import retime_chapters


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.run.mkdir()
        self.words = [{"word_id": index, "word": word, "start_ms": start,
                       "end_ms": start + 200, "flags": []}
                      for index, (word, start) in enumerate(
                          (("Hello", 261), ("Summaries", 29521), ("Drafts", 56002)))]
        self.alignment = {"source": "synthetic-test", "model": "test",
                          "granularity": "word", "duration_seconds": 90,
                          "flagged_word_count": 0, "words": self.words}
        self.word_map = self.root / "words.json"
        self.word_map.write_text(json.dumps(self.alignment))
        self.copy = {"titles": ["Example tutorial"], "description": "First paragraph.\n\nSecond paragraph.",
                     "keywords": ["summary", "draft replies"], "chapters": [
                         {"word_id": index, "title": title} for index, title in
                         enumerate(("Introduction", "Summaries", "Draft replies"))]}
        self.argv = ["local_generate.py", "--directory", str(self.run),
                     "--word-map", str(self.word_map), "--model", "test:local"]

    def generate(self, models=None):
        models = models if models is not None else [{"name": "test:local"}]
        response = {"done_reason": "stop", "message": {"content": json.dumps(self.copy)}}
        with patch("sys.argv", self.argv), patch.object(
            local_generate, "local_request", side_effect=[{"models": models}, response]
        ) as request, contextlib.redirect_stdout(io.StringIO()):
            local_generate.main()
        return request

    def test_generation_resources_and_retiming(self):
        request = self.generate()
        self.assertEqual(request.call_count, 2)
        prompt = request.call_args_list[1].args[1]["messages"][1]["content"]
        for word in self.words:
            self.assertIn(f"{word['word_id']} {word['word']}", prompt)
        payload = json.loads((self.run / "publishing-prep.json").read_text())
        self.assertEqual([chapter["start_ms"] for chapter in payload["chapters"]], [261, 29521, 56002])
        resource = {"title": "AI_COMPLETE", "url": "https://docs.snowflake.com/en/sql-reference/functions/ai_complete",
                    "relevance": "Synthetic test fixture, not a network verification.",
                    "verified_on": "2026-10-06", "verification_status": "content_verified",
                    "sources": ["test"]}
        manifest = self.root / "resources.json"
        manifest.write_text(json.dumps({"resources": [resource]}))
        with patch("sys.argv", ["attach_resources.py", "--directory", str(self.run),
                               "--resources", str(manifest)]), contextlib.redirect_stdout(io.StringIO()):
            attach_resources.main()
        final = json.loads((self.run / "publishing-prep.json").read_text())
        text = (self.run / "youtube-description.txt").read_text()
        self.assertEqual(final["youtube_description"], text)
        self.assertIn(self.copy["description"], text)
        self.assertIn("0:00 Introduction\n0:29 Summaries\n0:56 Draft replies", text)
        self.assertIn(resource["url"], text)
        markdown = (self.run / "publishing-prep.md").read_text()
        self.assertIn("summary, draft replies", markdown)
        self.assertIn(resource["url"], markdown)
        anchors = self.root / "anchors.json"
        anchors.write_text(json.dumps([{"word_id": word["word_id"], "expected_word": word["word"]}
                                      for word in self.words]))
        output = self.root / "retimed"
        with patch("sys.argv", ["retime_chapters.py", "--publishing-copy", str(self.run / "publishing-prep.json"),
                               "--word-map", str(self.word_map), "--anchors", str(anchors),
                               "--output-dir", str(output)]), contextlib.redirect_stdout(io.StringIO()):
            retime_chapters.main()
        retimed = json.loads((output / "publishing-prep.json").read_text())
        self.assertEqual(retimed["chapters"], final["chapters"])
        self.assertEqual(retimed["description"], self.copy["description"])

    def test_existing_artifacts_are_not_overwritten(self):
        target = self.run / "publishing-prep.md"
        target.write_text("Existing copy")
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            self.generate()
        self.assertEqual(target.read_text(), "Existing copy")

    def test_remote_model_is_rejected_before_generation(self):
        with self.assertRaisesRegex(ValueError, "not a cloud model"):
            self.generate([{"name": "test:local", "remote_host": "https://example.invalid"}])
        self.assertFalse((self.run / "transcript.json").exists())


if __name__ == "__main__":
    unittest.main()