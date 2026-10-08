# Shared SFGuide Workflow Contract

The `sfguide-verify` package owns the single mechanical validator and packaging implementation. Install it for all three workflows. Resolve its actual installation path using skill discovery; do not assume skills are siblings or that a working-directory-relative path is valid. This document and the helper ship inside that package.

## Installation

Use Python 3.10+ in an isolated environment with the package dependencies from `pyproject.toml`. After user approval when installation is necessary:

```bash
python3 -m venv "<tools-env>"
"<tools-env>/bin/python" -m pip install "<verify-skill>"
```

Use that interpreter for commands below. Do not run tests or guide code simply to inspect a notebook. The helper uses CommonMark parsing and has no network or guide-execution functionality.

## Paths and Source States

`validate` accepts an exact `.md` file, its containing folder, or a parent containing one unambiguous guide. Ambiguous input fails rather than choosing a guide silently. The ID, filename, and containing directory must agree. Missing assets are allowed if no images refer to them. Referenced images must be local raster files under `assets/`; symlinks, traversal, remote image URLs, unused assets, and unsupported formats are blockers requiring explicit remediation.

The companion is optional. `--companion` snapshots one source file or an exact Git root (tracked and non-ignored untracked files). Submodules and symlinks require separate handling; the tool fails closed. Include all executable inputs in the verified source. Ignored files, remote data, environment changes, and external dependencies are not tracked by these hashes; execution evidence must describe them. Do not store reports inside the companion repository unless its local-state folder is ignored, or writing a report will itself change the snapshot.

Supply actual `--current-repo` and `--target-repo` HTTPS GitHub URLs; arbitrary repository names and already-transferred repositories are supported. These describe state, not authorization to publish. With no companion, repository checks are N/A. Local-only projects can be audited without uploading anything. If shipping requires a public companion, obtain permission and establish its destination before recording publication-ready synchronization/link evidence.

## Report Contract

Reports contain schema/policy version, canonical paths, guide ID, current/target repository URLs, SHA-256 hashes of the guide and referenced assets, companion source hashes, and five checks:

- `mechanical`: computed by the helper; PASS or FAIL.
- `execution`: manual evidence for all applicable run/deploy paths; N/A only if none exist.
- `repo_sync`: manual local/remote revision comparison; N/A only without any companion.
- `links`: actual destination checks, not an assumption that URLs work.
- `disclosure`: review of everything intended for distribution.

Manual checks start UNTESTED except a truly absent companion's repo_sync. Reports are local evidence, not signed attestations or proof against deliberate tampering. Never store secrets or embed reports in the distributable guide. A fresh `validate` resets manual checks; it does not turn an old report green.

```bash
python "<verify-skill>/scripts/guide_tools.py" validate "<guide-file>" --report "<local-state>/report-01.json"
python "<verify-skill>/scripts/guide_tools.py" attest "<local-state>/report-01.json" --output "<local-state>/report-02.json" --check execution --status PASS --evidence "Tested the documented local commands; expected output matched; no resources remained."
```

Repeat `attest` for other checks only after doing the work. Evidence should reference test logs, actual remote commits where relevant, limitations, and cleanup. `attest` does not run tests or grant permission. N/A is forbidden for links and disclosure. All commands use exclusive output creation: choose a new path instead of overwriting evidence.

## Draft and Release Packaging

Drafts may contain UNTESTED manual checks, but mechanical failures block both modes. Label draft deliveries clearly and disclose pending checks.

```bash
python "<verify-skill>/scripts/guide_tools.py" package "<local-state>/report.json" --draft --output "<local-state>/guide-draft.zip"
```

Release packaging requires all applicable checks PASS and only justified N/A results. The helper recomputes mechanical checks and hashes before recording evidence or packaging; changed source is rejected. It packages only the guide markdown and referenced images, not `_local`, reports, source code, caches, or unrelated files.

```bash
python "<verify-skill>/scripts/guide_tools.py" package "<local-state>/final-report.json" --output "<local-state>/guide-release.zip"
python "<verify-skill>/scripts/guide_tools.py" check-delivery "<local-state>/final-report.json" "<local-state>/guide-release.zip" --staged "<submission-root>/<guide-id>"
```

`--staged` is the copied guide directory, not the whole monorepo. Inventory and bytes must match, with no extra files. Run it immediately before publishing; any later edit requires revalidation and a new ZIP. The helper does not examine the Git index, so separately confirm the committed PR files match these staged working files. Do not use broad `git add .` in a shared checkout. Final PR diff review remains mandatory.