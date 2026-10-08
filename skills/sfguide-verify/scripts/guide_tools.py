"""Local validation and packaging. Never executes guide code or uses the network."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

from markdown_it import MarkdownIt

SCHEMA = 1
POLICY = "sfguide-v1"
MANUAL = ("execution", "repo_sync", "links", "disclosure")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def resolve_guide(value):
    path = Path(value).expanduser().absolute()
    if path.is_symlink():
        raise ValueError("Guide input must not be a symlink")
    if path.is_dir():
        candidates = list(path.glob("*.md"))
        if not candidates:
            candidates = list(path.glob("*/*.md"))
        if len(candidates) != 1:
            raise ValueError("Provide the exact guide markdown path; folder is ambiguous or empty")
        path = candidates[0]
    if path.suffix != ".md" or not path.is_file() or path.is_symlink():
        raise ValueError("Guide must be a regular .md file")
    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError("Guide path must not traverse symlinks")
    return path.resolve()


def header_and_body(text):
    header, separator, body = text.partition("\n\n")
    if not separator:
        raise ValueError("Expected a plain metadata header followed by a blank line")
    metadata = {}
    for line in header.splitlines():
        key, delimiter, value = line.partition(":")
        if not delimiter or key in metadata:
            raise ValueError("Invalid or duplicate guide metadata")
        metadata[key] = value.strip()
    return metadata, body


def walk(tokens):
    for token in tokens:
        yield token
        yield from walk(token.children or [])


def local_asset(guide_dir, reference):
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise ValueError("Images must use local assets/ paths")
    relative = Path(unquote(parsed.path))
    if relative.is_absolute() or not relative.parts or relative.parts[0] != "assets" or ".." in relative.parts:
        raise ValueError("Image paths must stay inside assets/")
    candidate = guide_dir / relative
    if any(part.is_symlink() for part in [candidate, *candidate.parents]):
        raise ValueError("Image paths must not traverse symlinks")
    if not candidate.is_file():
        raise ValueError(f"Missing image: {reference}")
    if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("Only raster image assets are packaged")
    return candidate


def inspect(guide_file):
    text = guide_file.read_text(encoding="utf-8")
    metadata, body = header_and_body(text)
    errors = []
    guide_id = metadata.get("id", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", guide_id):
        errors.append("ID must be lowercase and hyphenated")
    if guide_id != guide_file.stem or guide_id != guide_file.parent.name:
        errors.append("ID, markdown filename and containing folder must agree")
    for key in ("author", "summary", "language", "categories", "status", "feedback link"):
        if not metadata.get(key):
            errors.append(f"Missing metadata: {key}")
    if metadata.get("status") != "Published":
        errors.append("Publication status must be Published")
    if metadata.get("language") not in {"en", "es", "it", "fr", "ja", "ko", "pt_br"}:
        errors.append("Unsupported language")
    categories = [item.strip() for item in metadata.get("categories", "").split(",")]
    if "snowflake-site:taxonomy/solution-center/certification/quickstart" not in categories:
        errors.append("Missing quickstart category")

    tokens = MarkdownIt("commonmark").parse(body)
    headings = [(token.tag, tokens[index + 1].content) for index, token in enumerate(tokens) if token.type == "heading_open"]
    if sum(level == "h1" for level, title in headings) != 1:
        errors.append("Exactly one article title is required")
    for level, title in headings:
        if int(level[1]) > 4:
            errors.append("Heading exceeds H4")
        if level == "h2" and len(title.split()) > 4:
            errors.append("H2 exceeds four words")
    for level, title in (("h2", "Overview"), ("h3", "What You'll Learn"), ("h3", "What You'll Build"), ("h3", "Prerequisites"), ("h2", "Conclusion And Resources")):
        if (level, title) not in headings:
            errors.append(f"Missing section: {title}")

    assets = set()
    for token in walk(tokens):
        if token.type in {"html_block", "html_inline"}:
            errors.append("HTML is not allowed")
        if token.type == "text":
            if re.search("[—–]", token.content):
                errors.append("Use plain punctuation in prose (code is excluded)")
            if re.search(r"\b(?:TODO|FIXME)\b|\bDuration:", token.content):
                errors.append("Unresolved placeholder or Duration tag in prose")
        if token.type == "image":
            try:
                assets.add(local_asset(guide_file.parent, token.attrGet("src") or ""))
            except ValueError as error:
                errors.append(str(error))
    assets_dir = guide_file.parent / "assets"
    if assets_dir.is_symlink():
        errors.append("assets must not be a symlink")
    elif assets_dir.exists():
        for candidate in assets_dir.rglob("*"):
            if candidate.is_symlink() or (candidate.is_file() and candidate not in assets):
                errors.append(f"Unreferenced or unsafe asset: {candidate.relative_to(guide_file.parent)}")
    files = {str(path.relative_to(guide_file.parent)): digest(path.read_bytes()) for path in sorted({guide_file, *assets})}
    return metadata, files, sorted(set(errors))


def companion_snapshot(value):
    if value is None:
        return None
    path = Path(value).expanduser().absolute()
    if any(candidate.is_symlink() for candidate in [path, *path.parents]):
        raise ValueError("Companion path must not traverse symlinks")
    path = path.resolve(strict=True)
    if path.is_file():
        return {"path": str(path), "files": {path.name: digest(path.read_bytes())}}
    # Git's index + untracked, non-ignored files includes working edits without
    # hashing virtualenvs and other ignored build products. Require an exact root.
    root = subprocess.check_output(["git", "-C", str(path), "rev-parse", "--show-toplevel"], text=True).strip()
    if Path(root).resolve() != path:
        raise ValueError("Companion directory must be its Git repository root, or provide one source file")
    names = subprocess.check_output(["git", "-C", str(path), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]).decode().split("\0")
    files = {}
    for name in sorted(set(filter(None, names))):
        candidate = path / name
        if any(part.is_symlink() for part in [candidate, *candidate.parents]):
            raise ValueError("Companion snapshot cannot contain symlinks")
        if candidate.exists() and not candidate.is_file():
            raise ValueError("Submodules require separate verification evidence")
        files[name] = digest(candidate.read_bytes()) if candidate.exists() else "DELETED"
    return {"path": str(path), "files": files}


def repo_url(value):
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed.path) or parsed.query or parsed.fragment:
        raise ValueError("Repository URL must be https://github.com/owner/repository")
    return value.rstrip("/")


def make_report(guide, companion=None, current_repo=None, target_repo=None):
    guide_file = resolve_guide(guide)
    metadata, files, errors = inspect(guide_file)
    checks = {name: {"status": "UNTESTED", "evidence": "Not performed by the mechanical validator"} for name in MANUAL}
    checks["mechanical"] = {"status": "FAIL" if errors else "PASS", "evidence": errors or ["Mechanical checks passed; manual checks remain separate"]}
    if companion is None and current_repo is None and target_repo is None:
        checks["repo_sync"] = {"status": "N/A", "evidence": "No companion source or repository supplied"}
    return {
        "schema_version": SCHEMA, "policy_version": POLICY,
        "guide_file": str(guide_file), "guide_dir": str(guide_file.parent),
        "assets_dir": str(guide_file.parent / "assets"), "guide_id": metadata.get("id"),
        "files": files, "companion": companion_snapshot(companion),
        "current_repo_url": repo_url(current_repo), "target_repo_url": repo_url(target_repo),
        "checks": checks,
    }


def outside_guide(path, report):
    resolved = Path(path).expanduser().resolve()
    if resolved.is_relative_to(Path(report["guide_dir"])):
        raise ValueError("Reports and archives must remain outside the guide directory")
    return resolved


def save_new(path, report):
    destination = outside_guide(path, report)
    with destination.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")


def load_fresh(path):
    report = json.loads(Path(path).read_text())
    if report.get("schema_version") != SCHEMA or report.get("policy_version") != POLICY:
        raise ValueError("Report schema/policy changed; revalidate")
    companion = report.get("companion")
    current = make_report(report["guide_file"], companion["path"] if companion else None, report.get("current_repo_url"), report.get("target_repo_url"))
    for key in ("guide_id", "guide_dir", "files", "companion"):
        if report.get(key) != current[key]:
            raise ValueError(f"Stale verification ({key}); regenerate report and rerun checks")
    if current["checks"]["mechanical"]["status"] != "PASS":
        raise ValueError("Mechanical checks fail; revalidate")
    return report


def require_release(report):
    if set(report["checks"]) != {*MANUAL, "mechanical"}:
        raise ValueError("Missing or unknown verification checks")
    for name, result in report["checks"].items():
        if result.get("status") not in {"PASS", "N/A"} or not result.get("evidence"):
            raise ValueError(f"Release blocked: {name}")
        if result["status"] == "N/A" and name not in {"execution", "repo_sync"}:
            raise ValueError(f"N/A is not allowed for {name}")


def attest(report_path, output, check, status, evidence):
    report = load_fresh(report_path)
    if check not in MANUAL or status not in {"PASS", "FAIL", "UNTESTED", "N/A"} or not evidence.strip():
        raise ValueError("Invalid attestation")
    if status == "N/A" and (check not in {"execution", "repo_sync"} or (check == "repo_sync" and any(report.get(key) for key in ("companion", "current_repo_url", "target_repo_url")))):
        raise ValueError("This check is applicable and cannot be N/A")
    report["checks"][check] = {"status": status, "evidence": evidence.strip()}
    save_new(output, report)
    return report


def package(report_path, output, draft=False):
    report = load_fresh(report_path)
    if not draft:
        require_release(report)
    destination = outside_guide(output, report)
    payload = {}
    for name, expected in report["files"].items():
        data = (Path(report["guide_dir"]) / name).read_bytes()
        if digest(data) != expected:
            raise ValueError("Content changed during packaging")
        payload[f"{report['guide_id']}/{name}"] = data
    # All validation precedes file creation. Exclusive creation avoids clobbering.
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    return {"kind": "DRAFT" if draft else "RELEASE", "archive": str(destination), "sha256": digest(destination.read_bytes())}


def check_delivery(report_path, archive_path, staged=None):
    report = load_fresh(report_path)
    require_release(report)
    expected = {f"{report['guide_id']}/{name}": value for name, value in report["files"].items()}
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError("Archive inventory differs from verified files")
        if any(digest(archive.read(name)) != value for name, value in expected.items()):
            raise ValueError("Archive content differs from verified files")
    if staged:
        directory = Path(staged).absolute()
        if any(path.is_symlink() for path in [directory, *directory.parents]):
            raise ValueError("Staged guide path must not traverse symlinks")
        if not directory.is_dir():
            raise ValueError("Staged guide directory does not exist")
        directory = directory.resolve()
        candidates = list(directory.rglob("*"))
        if any(path.is_symlink() for path in candidates):
            raise ValueError("Staged guide contains a symlink")
        files = {str(path.relative_to(directory)): digest(path.read_bytes()) for path in candidates if path.is_file()}
        if files != report["files"]:
            raise ValueError("Staged guide differs from verified files")
    return {"status": "PASS", "scope": "Archive and supplied staged guide match current verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("guide")
    validate.add_argument("--report", required=True)
    validate.add_argument("--companion")
    validate.add_argument("--current-repo")
    validate.add_argument("--target-repo")
    evidence = commands.add_parser("attest", help="Record human/agent evidence; does not execute the check")
    evidence.add_argument("report")
    evidence.add_argument("--output", required=True)
    evidence.add_argument("--check", choices=MANUAL, required=True)
    evidence.add_argument("--status", choices=("PASS", "FAIL", "UNTESTED", "N/A"), required=True)
    evidence.add_argument("--evidence", required=True)
    bundle = commands.add_parser("package")
    bundle.add_argument("report")
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--draft", action="store_true")
    delivery = commands.add_parser("check-delivery")
    delivery.add_argument("report")
    delivery.add_argument("archive")
    delivery.add_argument("--staged")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            result = make_report(args.guide, args.companion, args.current_repo, args.target_repo)
            save_new(args.report, result)
        elif args.command == "attest":
            result = attest(args.report, args.output, args.check, args.status, args.evidence)
        elif args.command == "package":
            result = package(args.report, args.output, args.draft)
        else:
            result = check_delivery(args.report, args.archive, args.staged)
        print(json.dumps(result, indent=2))
        if args.command == "validate" and result["checks"]["mechanical"]["status"] == "FAIL":
            parser.exit(1)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()