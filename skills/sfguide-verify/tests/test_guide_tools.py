import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guide_tools.py"
SPEC = importlib.util.spec_from_file_location("guide_tools", SCRIPT)
tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tools)

GUIDE = """author: Example Author
id: example-guide
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
language: en
summary: Run a local example.
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Run a Local Example

## Overview

### What You'll Learn
Run Python.

### What You'll Build
A local example.

### Prerequisites
Python.

## Run the Example

Inline code: `print("10–30")`.

```python
print("10–30")
```

```text
10–30
```

## Conclusion And Resources

Congratulations! You've successfully run the example.
"""


class GuideToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.directory = self.root / "example-guide"
        self.directory.mkdir()
        self.guide = self.directory / "example-guide.md"
        self.guide.write_text(GUIDE)
        self.report = self.root / "report.json"

    def tearDown(self):
        self.temp.cleanup()

    def validate(self, **kwargs):
        report = tools.make_report(self.guide, **kwargs)
        tools.save_new(self.report, report)
        return report

    def release(self, **kwargs):
        self.validate(**kwargs)
        path = self.report
        for index, check in enumerate(("execution", "links", "disclosure")):
            output = self.root / f"evidence-{index}.json"
            tools.attest(path, output, check, "PASS", f"Synthetic fixture evidence for {check}; not a live product test")
            path = output
        return path

    def test_file_folder_and_parent_resolve_identically(self):
        for value in (self.guide, self.directory, self.root):
            self.assertEqual(tools.resolve_guide(value), self.guide)

    def test_ambiguous_parent_rejected(self):
        other = self.root / "other"
        other.mkdir()
        (other / "other.md").write_text(GUIDE)
        with self.assertRaises(ValueError):
            tools.resolve_guide(self.root)

    def test_no_assets_and_no_companion_pass(self):
        report = self.validate()
        self.assertEqual(report["checks"]["mechanical"]["status"], "PASS")
        self.assertEqual(report["checks"]["repo_sync"]["status"], "N/A")
        self.assertFalse((self.directory / "assets").exists())

    def test_code_and_expected_output_are_not_prose(self):
        self.assertEqual(self.validate()["checks"]["mechanical"]["status"], "PASS")

    def test_prose_dash_fails(self):
        self.guide.write_text(GUIDE + "\nIncorrect—prose\n")
        self.assertEqual(self.validate()["checks"]["mechanical"]["status"], "FAIL")

    def test_inline_html_fails_but_fenced_html_is_allowed(self):
        self.guide.write_text(GUIDE + "\n```html\n<div>example</div>\n```\n")
        self.assertEqual(tools.make_report(self.guide)["checks"]["mechanical"]["status"], "PASS")
        self.guide.write_text(GUIDE + "\n<div>example</div>\n")
        self.assertEqual(tools.make_report(self.guide)["checks"]["mechanical"]["status"], "FAIL")

    def test_missing_reference_image_fails(self):
        self.guide.write_text(GUIDE + "\n![Example][sample]\n\n[sample]: assets/missing.png\n")
        self.assertEqual(self.validate()["checks"]["mechanical"]["status"], "FAIL")

    def test_referenced_asset_packaged_unrelated_files_excluded(self):
        assets = self.directory / "assets"
        assets.mkdir()
        (assets / "sample.png").write_bytes(b"synthetic image bytes")
        (self.directory / ".env").write_text("NOT_A_REAL_SECRET=test")
        self.guide.write_text(GUIDE + "\n![Example](assets/sample.png)\n")
        report = self.release()
        archive = self.root / "release.zip"
        tools.package(report, archive)
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(set(bundle.namelist()), {"example-guide/example-guide.md", "example-guide/assets/sample.png"})

    def test_unused_asset_blocks_packaging(self):
        assets = self.directory / "assets"
        assets.mkdir()
        (assets / "private.txt").write_text("not for publication")
        self.validate()
        with self.assertRaises(ValueError):
            tools.package(self.report, self.root / "draft.zip", draft=True)

    def test_traversal_and_remote_image_rejected(self):
        for image in ("assets/../outside.png", "assets/%2e%2e/outside.png", "https://example.com/image.png"):
            self.guide.write_text(GUIDE + f"\n![Image]({image})\n")
            self.assertEqual(tools.make_report(self.guide)["checks"]["mechanical"]["status"], "FAIL")

    def test_symlink_image_rejected(self):
        assets = self.directory / "assets"
        assets.mkdir()
        target = self.root / "outside.png"
        target.write_bytes(b"private")
        (assets / "image.png").symlink_to(target)
        self.guide.write_text(GUIDE + "\n![Image](assets/image.png)\n")
        self.assertEqual(self.validate()["checks"]["mechanical"]["status"], "FAIL")

    def test_arbitrary_and_transferred_repository_preserved(self):
        url = "https://github.com/Snowflake-Labs/different-project-name"
        report = self.validate(current_repo=url, target_repo=url)
        self.assertEqual(report["current_repo_url"], url)
        self.assertEqual(report["checks"]["repo_sync"]["status"], "UNTESTED")
        with self.assertRaises(ValueError):
            tools.attest(self.report, self.root / "na.json", "repo_sync", "N/A", "skip")

    def test_repo_url_credentials_rejected(self):
        with self.assertRaises(ValueError):
            tools.make_report(self.guide, current_repo="https://token@github.com/owner/repo")

    def test_local_only_companion_is_supported(self):
        source = self.root / "example.py"
        source.write_text("print(1)\n")
        report = self.validate(companion=source)
        self.assertIsNone(report["current_repo_url"])
        self.assertEqual(report["checks"]["repo_sync"]["status"], "UNTESTED")

    def test_companion_changes_invalidate_report(self):
        source = self.root / "example.py"
        source.write_text("print(1)\n")
        self.validate(companion=source)
        source.write_text("print(2)\n")
        with self.assertRaisesRegex(ValueError, "Stale"):
            tools.load_fresh(self.report)

    def test_companion_symlink_rejected(self):
        source = self.root / "source.py"
        source.write_text("print(1)\n")
        link = self.root / "linked.py"
        link.symlink_to(source)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            tools.make_report(self.guide, companion=link)

    def test_git_companion_snapshot_catches_untracked_changes(self):
        project = self.root / "project"
        project.mkdir()
        subprocess.run(["git", "init", "--quiet", str(project)], check=True)
        (project / "example.py").write_text("print(1)\n")
        self.validate(companion=project)
        (project / "example.py").write_text("print(2)\n")
        with self.assertRaisesRegex(ValueError, "Stale"):
            tools.load_fresh(self.report)

    def test_draft_allowed_but_untested_release_blocked(self):
        self.validate()
        tools.package(self.report, self.root / "draft.zip", draft=True)
        with self.assertRaisesRegex(ValueError, "Release blocked"):
            tools.package(self.report, self.root / "release.zip")

    def test_failed_manual_check_blocks_release(self):
        self.validate()
        failed = self.root / "failed.json"
        tools.attest(self.report, failed, "execution", "FAIL", "Output differs")
        with self.assertRaises(ValueError):
            tools.package(failed, self.root / "release.zip")

    def test_no_na_for_links_or_disclosure(self):
        self.validate()
        for check in ("links", "disclosure"):
            with self.assertRaises(ValueError):
                tools.attest(self.report, self.root / f"{check}.json", check, "N/A", "skip")

    def test_post_verification_url_edit_requires_new_report(self):
        report = self.release()
        self.guide.write_text(GUIDE.replace("sfquickstarts/issues", "sfquickstarts/pulls"))
        with self.assertRaisesRegex(ValueError, "Stale"):
            tools.package(report, self.root / "release.zip")
        new_report = tools.make_report(self.guide)
        self.assertEqual(new_report["checks"]["execution"]["status"], "UNTESTED")

    def test_asset_edit_invalidates_report(self):
        assets = self.directory / "assets"
        assets.mkdir()
        image = assets / "sample.png"
        image.write_bytes(b"first")
        self.guide.write_text(GUIDE + "\n![Example](assets/sample.png)\n")
        self.validate()
        image.write_bytes(b"second")
        with self.assertRaisesRegex(ValueError, "Stale"):
            tools.package(self.report, self.root / "draft.zip", draft=True)

    def test_delivery_matches_and_detects_stale_zip_and_extra_files(self):
        report = self.release()
        archive = self.root / "release.zip"
        tools.package(report, archive)
        staging = self.root / "staged"
        shutil.copytree(self.directory, staging)
        self.assertEqual(tools.check_delivery(report, archive, staging)["status"], "PASS")
        (staging / "private.txt").write_text("unexpected")
        with self.assertRaisesRegex(ValueError, "Staged"):
            tools.check_delivery(report, archive, staging)
        bad = self.root / "stale.zip"
        with zipfile.ZipFile(bad, "w") as bundle:
            bundle.writestr("example-guide/example-guide.md", "old content")
        with self.assertRaisesRegex(ValueError, "Archive content"):
            tools.check_delivery(report, bad)

    def test_reports_and_archives_outside_guide_and_no_overwrite(self):
        report = self.validate()
        with self.assertRaises(ValueError):
            tools.save_new(self.directory / "report.json", report)
        with self.assertRaises(FileExistsError):
            tools.save_new(self.report, report)
        archive = self.root / "draft.zip"
        tools.package(self.report, archive, draft=True)
        with self.assertRaises(FileExistsError):
            tools.package(self.report, archive, draft=True)
        with self.assertRaises(ValueError):
            tools.package(self.report, self.directory / "draft.zip", draft=True)

    def test_staged_root_symlink_rejected(self):
        report = self.release()
        archive = self.root / "release.zip"
        tools.package(report, archive)
        link = self.root / "staging-link"
        link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            tools.check_delivery(report, archive, link)

    def test_release_then_new_validation_does_not_reuse_old_attestations(self):
        report = self.release()
        archive = self.root / "release.zip"
        tools.package(report, archive)
        self.guide.write_text(GUIDE + "\nReviewed new content.\n")
        fresh = self.root / "fresh.json"
        tools.save_new(fresh, tools.make_report(self.guide))
        with self.assertRaisesRegex(ValueError, "Release blocked"):
            tools.package(fresh, self.root / "new-release.zip")
        self.assertEqual(json.loads(fresh.read_text())["checks"]["links"]["status"], "UNTESTED")

    def test_cli_create_verify_ship_local_acceptance(self):
        def command(*args, success=True):
            result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, success, result.stderr)
            return json.loads(result.stdout) if success else None

        command("validate", self.directory, "--report", self.report)
        command("package", self.report, "--draft", "--output", self.root / "draft.zip")
        executed = subprocess.run([sys.executable, "-c", 'print("10–30")'], check=True, capture_output=True, text=True)
        self.assertEqual(executed.stdout, "10–30\n")
        report = self.report
        for check in ("execution", "links", "disclosure"):
            next_report = self.root / f"cli-{check}.json"
            command("attest", report, "--output", next_report, "--check", check, "--status", "PASS", "--evidence", "Synthetic acceptance evidence; links/disclosure stubbed, not live verification")
            report = next_report
        archive = self.root / "final.zip"
        command("package", report, "--output", archive)
        staged = self.root / "submission"
        shutil.copytree(self.directory, staged)
        command("check-delivery", report, archive, "--staged", staged)
        self.guide.write_text(GUIDE + "\nChanged after verification.\n")
        command("check-delivery", report, archive, "--staged", staged, success=False)


if __name__ == "__main__":
    unittest.main()