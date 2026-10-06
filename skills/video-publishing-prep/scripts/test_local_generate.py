import unittest

from local_generate import timestamp, validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.words = [{"word_id": index, "word": "Example", "start_ms": start,
                       "end_ms": start + 100, "flags": []}
                      for index, start in enumerate((700, 12500, 12800))]
        self.copy = {"titles": ["Example title"], "description": "Example description",
                     "keywords": ["example"], "chapters": [
                         {"word_id": 0, "title": "Intro"},
                         {"word_id": 1, "title": "Demo"}]}

    def test_resolves_exact_word_times(self):
        result = validate(self.copy, self.words, 20)
        self.assertEqual(result[1]["start_seconds"], 12.5)
        self.assertEqual(result[0]["start_ms"], 700)
        self.assertEqual(result[0]["youtube_start_seconds"], 0)
        self.assertEqual(timestamp(12.5), "0:12")
        self.assertEqual(timestamp(3661), "1:01:01")

    def test_rejects_invalid_ids(self):
        for word_id in (True, -1, 4, "1", 0.5):
            with self.subTest(word_id=word_id):
                self.copy["chapters"][1]["word_id"] = word_id
                with self.assertRaises(ValueError):
                    validate(self.copy, self.words, 20)

    def test_rejects_out_of_order_and_end_of_media(self):
        for word_id in (0, 3):
            self.copy["chapters"][1]["word_id"] = word_id
            with self.assertRaises(ValueError):
                validate(self.copy, self.words, 20)

    def test_rejects_whole_second_collision(self):
        self.copy["chapters"] = [{"word_id": 0, "title": "Intro"},
                                 {"word_id": 1, "title": "First"},
                                 {"word_id": 2, "title": "Second"}]
        with self.assertRaises(ValueError):
            validate(self.copy, self.words, 20)

    def test_rejects_missing_intro(self):
        self.copy["chapters"] = [{"word_id": 1, "title": "First"}]
        with self.assertRaises(ValueError):
            validate(self.copy, self.words, 20)

    def test_rejects_long_title(self):
        self.copy["titles"] = ["x" * 101]
        with self.assertRaises(ValueError):
            validate(self.copy, self.words, 20)

    def test_rejects_empty_fields(self):
        for key, value in (("titles", []), ("description", ""), ("keywords", []), ("chapters", [])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate({**self.copy, key: value}, self.words, 20)

    def test_rejects_unaligned_or_flagged_word(self):
        for flags, start in ((["low_alignment_score"], 12500), ([], None)):
            self.words[1].update(flags=flags, start_ms=start)
            with self.assertRaises(ValueError):
                validate(self.copy, self.words, 20)


if __name__ == "__main__":
    unittest.main()