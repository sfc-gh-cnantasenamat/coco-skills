import unittest
from attach_resources import add_markdown, description, validate_resources


class ResourcesTests(unittest.TestCase):
    def setUp(self):
        self.resource = {"title": "Official guide", "url": "https://docs.snowflake.com/en/example",
                         "relevance": "Supports the demonstrated topic.", "verified_on": "2026-10-01",
                         "sources": ["snowflake_product_docs"], "verification_status": "content_verified"}

    def test_accepts_verified_official_pages(self):
        self.assertEqual(validate_resources({"resources": [self.resource]}), [self.resource])

    def test_rejects_unofficial_or_unverified(self):
        for url in ("http://docs.snowflake.com/x", "https://docs.snowflake.com.evil.org/x",
                    "https://user@docs.streamlit.io/x", "https://docs.streamlit.io:444/x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_resources({"resources": [{**self.resource, "url": url}]})
        with self.assertRaises(ValueError):
            validate_resources({"resources": [{**self.resource, "verification_status": "search_only"}]})

    def test_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            validate_resources({"resources": [self.resource, self.resource]})

    def test_idempotent_markdown(self):
        first = add_markdown("# Existing copy\n", [self.resource])
        self.assertEqual(add_markdown(first, [self.resource]), first)

    def test_description_uses_display_times(self):
        text = description({"description": "Summary", "chapters": [
            {"start_seconds": 0.702, "youtube_start_seconds": 0, "title": "Intro"}],
            "resources": [self.resource], "hashtags": ["#Snowflake"]})
        self.assertIn("0:00 Intro", text)
        self.assertIn(self.resource["url"], text)
        self.assertIn("RESOURCES", text)


if __name__ == "__main__":
    unittest.main()