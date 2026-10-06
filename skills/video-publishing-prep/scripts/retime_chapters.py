"""Retain reviewed publishing copy and resolve chapters from explicit word IDs."""
import argparse
import json
from pathlib import Path

from local_generate import render, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publishing-copy", type=Path, required=True)
    parser.add_argument("--word-map", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    original = json.loads(args.publishing_copy.read_text())
    alignment = json.loads(args.word_map.read_text())
    anchors = json.loads(args.anchors.read_text())
    if alignment.get("granularity") != "word":
        raise ValueError("Expected a word-level alignment")
    if len(anchors) != len(original["chapters"]):
        raise ValueError("One explicit word ID is required for each chapter")
    copy = {**original, "chapters": [
        {"title": chapter["title"], "word_id": anchor["word_id"]}
        for chapter, anchor in zip(original["chapters"], anchors)
    ]}
    words = alignment["words"]
    for anchor in anchors:
        word_id = anchor["word_id"]
        if type(word_id) is not int or not 0 <= word_id < len(words):
            raise ValueError("Invalid word ID")
        if words[word_id]["word"] != anchor["expected_word"]:
            raise ValueError("Anchor word mismatch: source may have changed")
    copy["chapters"] = validate(copy, words, alignment["duration_seconds"])
    copy["timing"] = {key: value for key, value in alignment.items() if key != "words"}
    copy["timing"]["word_map"] = str(args.word_map.resolve())
    copy["timing"]["chapter_rule"] = "start_ms equals anchor word start_ms; floor only YouTube display; intro displays 0"
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "publishing-prep.json").write_text(json.dumps(copy, indent=2) + "\n")
    markdown = render(copy)
    markdown += "\n## Word-level chapter anchors\n\n| Chapter | Word ID | Opening word | Start (seconds) | Start (ms) |\n| --- | ---: | --- | ---: | ---: |\n"
    for chapter in copy["chapters"]:
        markdown += f"| {chapter['title']} | {chapter['word_id']} | {chapter['anchor_word']} | {chapter['start_seconds']:.3f} | {chapter['start_ms']} |\n"
    markdown += f"\nThe supplied transcript has {len(words)} words; {alignment['flagged_word_count']} words need review. No chapter anchor is flagged. Full-transcript correctness has not been manually verified.\n"
    (args.output_dir / "publishing-prep.md").write_text(markdown)
    print(json.dumps(copy["chapters"], indent=2))


if __name__ == "__main__":
    main()