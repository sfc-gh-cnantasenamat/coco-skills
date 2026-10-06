"""Attach caller-verified official documentation without network requests."""
import argparse
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlsplit

from local_generate import timestamp


def validate_resources(manifest):
    resources = manifest.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ValueError("Verified documentation resources are required")
    seen = set()
    for resource in resources:
        for key in ("title", "url", "relevance", "verified_on"):
            if not isinstance(resource.get(key), str) or not resource[key].strip():
                raise ValueError(f"Missing resource {key}")
        url = urlsplit(resource["url"])
        if (url.scheme != "https" or url.hostname not in {"docs.snowflake.com", "docs.streamlit.io"}
                or url.username or url.password or url.port not in {None, 443}):
            raise ValueError("Only official HTTPS documentation URLs are allowed")
        if any(character.isspace() for character in resource["url"]) or resource["url"] in seen:
            raise ValueError("Malformed or duplicate documentation URL")
        if resource.get("verification_status") != "content_verified":
            raise ValueError("Read the destination content before attaching it")
        if not isinstance(resource.get("sources"), list) or not resource["sources"]:
            raise ValueError("Resource discovery provenance required")
        date.fromisoformat(resource["verified_on"])
        seen.add(resource["url"])
    return resources


def description(payload):
    chapters = "\n".join(f"{timestamp(chapter['youtube_start_seconds'])} {chapter['title']}"
                         for chapter in payload["chapters"])
    resources = "\n\n".join(f"{resource['title']}\n{resource['url']}" for resource in payload["resources"])
    parts = [payload["description"], "CHAPTERS\n" + chapters, "RESOURCES\n" + resources]
    if payload.get("hashtags"):
        parts.append(" ".join(payload["hashtags"]))
    text = "\n\n".join(parts) + "\n"
    if len(text) > 5000:
        raise ValueError("Description exceeds 5000 characters; curate fewer resources")
    return text


def add_markdown(text, resources):
    marker = "\n<!-- official-documentation:start -->"
    end_marker = "<!-- official-documentation:end -->"
    if marker in text:
        start = text.index(marker)
        end = text.index(end_marker, start) + len(end_marker)
        text = text[:start] + text[end:]
    lines = [marker, "## Official documentation", ""]
    for resource in resources:
        lines.append(f"- [{resource['title']}]({resource['url']}): {resource['relevance']}")
    lines.extend(["", "These are supporting documentation links, not the video's specific guide or sample repository.",
                  end_marker, ""])
    return text.rstrip() + "\n" + "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--resources", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.resources.read_text())
    resources = validate_resources(manifest)
    pending = []
    for folder in (args.directory, args.directory / "word-timed-publishing"):
        path = folder / "publishing-prep.json"
        if not path.exists():
            if folder == args.directory:
                raise FileNotFoundError(path)
            continue
        payload = json.loads(path.read_text())
        payload["resources"] = resources
        payload["documentation_lookup"] = manifest.get("lookup", {})
        payload["youtube_description"] = description(payload)
        markdown_path = folder / "publishing-prep.md"
        pending.extend([(path, json.dumps(payload, indent=2) + "\n"),
                        (markdown_path, add_markdown(markdown_path.read_text(), resources))])
        if folder == args.directory:
            pending.append((folder / "youtube-description.txt", payload["youtube_description"]))
    for path, text in pending:
        path.write_text(text)
    print(f"Attached {len(resources)} verified official resources; updated {len(pending)} files.")


if __name__ == "__main__":
    main()