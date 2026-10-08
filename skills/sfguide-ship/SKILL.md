---
name: sfguide-ship
id: sfguide-ship
title: Ship a Snowflake Guide
summary: Verify, polish, and open PRs for a Snowflake developer guide and its companion repo in Snowflake-Labs.
description: "End-to-end workflow for shipping a Snowflake sfguide (quickstart) and its companion project: delegates verification to sfguide-verify, then handles content polish, humanizing language, a pre-review checkpoint, repo hand-off, and pushing PRs to Snowflake-Labs repos. Use when: ship sfguide, publish sfguide, push quickstart, sfguide is ready to ship, submit sfguide, ready to publish quickstart, ship the guide, sfguide shipping checklist. Triggers: ship sfguide, publish sfguide, submit quickstart, push sfguide, sfguide done, ready to ship, sfguide PR. Do NOT use for drafting a new guide or for verification only (use sfguide-verify)."
authors: Chanin Nantasenamat
type: snowflake
status: beta
categories:
  - documentation
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
prompt: "Ship my sfguide at ~/guides/my-guide"
language: en
---

# SFGuide Ship

## Purpose

Polish + publish pipeline for an sfguide and its companion project. Delegates verification and fixes to `sfguide-verify`, then runs sequential stages: companion repo hand-off, content/clarity audit, architecture diagram, humanizing, a pre-review checkpoint, repo setup confirmation, and pushing PRs to `Snowflake-Labs/sfquickstarts` and `Snowflake-Labs/snowflake-demo-notebooks`.

Placeholders used below:
- `<your-github-user>`: the GitHub account that hosts the staging repos and the forks
- `<sfquickstarts-clone>`: local clone of your `sfquickstarts` fork

---

## Setup

Ask user:
```
To start the shipping checklist, please provide:
1. Path to the sfguide folder (containing <id>/<id>.md and assets/)
2. Path to the companion project/notebook (if separate from the guide folder)
3. Your GitHub user (where the staging repos and forks live)
4. Path to your local sfquickstarts fork clone
```

**STOP**: Wait for answers before proceeding.

Once paths are provided, verify they exist before doing anything else:

```bash
# Verify sfguide folder
ls "<sfguide-folder>/<id>/<id>.md"
ls "<sfguide-folder>/<id>/assets/"

# Verify companion project/notebook (if provided)
ls "<companion-path>"
```

If the companion project path does not exist, report it as missing and stop. If the sfguide folder/file does not exist, stop and ask the user to create the guide first (or provide the correct path). Do not proceed until all provided paths resolve to real files/folders.

**Derive `<id>` from the guide's frontmatter** (the `id:` field in `<id>/<id>.md`). This is the single naming key used for the rest of the pipeline: the companion repo is always `sfguide-<id>` (both pre- and post-transfer), and the quickstart path is always `sfquickstarts/site/sfguides/src/<id>/`. Don't substitute a different "name" anywhere -- if the folder name, frontmatter `id`, and any existing companion repo name disagree, flag it now and resolve it before continuing.

**The companion repo is built and lives at `<your-github-user>/sfguide-<id>` through verification and early shipping stages.** This is the canonical build location, not a temporary or mistaken state -- don't treat it as something to "fix" until the Stage 1 hand-off request. Check whether it already exists:

```bash
gh api repos/<your-github-user>/sfguide-<id> --jq '.html_url' 2>&1
```

If it doesn't exist yet, create it now so sfguide-verify has somewhere to push fixes.

**The guide itself is built and lives at `<your-github-user>/<id>` throughout the pipeline** -- a separate staging repo from the companion project, named without the `sfguide-` prefix (`sfguide-<id>` = code, `<id>` = guide markdown/assets). Unlike the companion repo, this one has no hand-off step: `sfquickstarts` is a shared monorepo. Stage 6 opens the PR into `Snowflake-Labs/sfquickstarts`, sourcing content from this staging repo. Check whether it already exists:

```bash
gh api repos/<your-github-user>/<id> --jq '.html_url' 2>&1
```

If it doesn't exist yet, create it now.

---

## Verification

**Load the `sfguide-verify` skill and run it** with the paths collected above. Wait for it to complete all 4 of its stages (readiness audit, end-to-end verification, sync check, fix blockers) before continuing.

After sfguide-verify completes, push any guide changes it produced to `<your-github-user>/<id>` (the guide's staging repo).

---

## Workflow

### Stage 1: Request Companion Repo Hand-off to Snowflake-Labs

Once the companion repo is verified and fixed (sfguide-verify completed), request the move to `Snowflake-Labs`:

1. Confirm the companion repo is fully pushed and up to date at `<your-github-user>/sfguide-<id>`.
2. Generate a short hand-off request for the user to send through whatever channel they use (ticket, Slack, etc.):
   ```
   Please transfer/add <your-github-user>/sfguide-<id> to the
   Snowflake-Labs org as Snowflake-Labs/sfguide-<id>.
   ```
3. **STOP**: Wait for the user to confirm the move has happened. Don't guess at or hardcode a specific mechanism (native `gh repo transfer` vs. a manual recreation by an org admin) -- the skill only cares whether the end state exists, checked in Stage 5.

This stage can be skipped if `Snowflake-Labs/sfguide-<id>` already exists (e.g., a prior run already completed the hand-off).

---

### Stage 2: Content and Clarity Audit

Review the guide for quality:
- Flow: does the narrative move logically from overview through conclusion?
- Ambiguity: are any steps vague about where to click, what to select, or what output to expect?
- Privilege notes: are any Snowflake role or permission requirements called out where needed?
- Wording: minor clarity, grammar, or consistency fixes

Produce a numbered list of suggested fixes.

**STOP**: Present suggestions. Apply only those the user approves.

---

### Stage 3: Architecture Diagram

Scan the guide for an architecture or system-flow diagram (in the Overview or a dedicated section). If none exists, ask the user:

```
This guide has no architecture diagram. Would you like to add one?
- Yes -> Generate a PNG diagram of the system (components, data flow, Snowflake
        objects involved) with a diagram skill or script, place it in assets/,
        and add an ![Architecture](assets/<name>.png) reference in the Overview section.
- No  -> Skip and continue.
```

If an architecture diagram already exists, check that it accurately reflects the current system (components, flow, object names) and flag any inaccuracies.

Keep the generator script for every generated image (diagrams, before/after graphics) in the guide staging repo under `_local/diagrams/`, outside the submission folder, never only in a temp directory. If a diagram needs regenerating and its script is gone, say so and rebuild the script there.

**STOP**: Present diagram findings or offer. Wait for user decision before continuing.

---

### Stage 4: Humanize the Language

Run a humanizing pass over the full guide text (use a humanizing skill if one is installed).

Goals:
- Strip AI-sounding phrasing (over-qualified hedging, robotic sentence structures, buzzwords)
- Ensure tone is direct and natural, consistent with the author's voice
- Do not change technical content, code blocks, or section headers

**STOP**: Present humanized sections for review before writing changes.

---

### Pre-Review Checkpoint

Run this whenever the user is about to share the guide for review (and before Stage 5):

1. Stop any local servers started during verification (`lsof -ti tcp:<port>`, then kill).
2. Rebuild the guide ZIP, excluding dot-folders (`.git`, `.DS_Store`) and `_local/`; confirm every image reference resolves.
3. Confirm both staging repos are pushed and clean (`git status -sb`).
4. Draft reviewer notes: links that 404 until the Stage 1 hand-off (and which staging repos to use meanwhile), Snowflake resources reviewers need (compute pool, external access integration, etc.), and any path not tested with the reader's actual tool.

**STOP**: Present the notes. Wait for the user before continuing.

---

### Stage 5: Confirm Repo Setup

**Pre-check 1 -- companion repo hand-off complete:**
```bash
gh api repos/Snowflake-Labs/sfguide-<id> --jq '.html_url' 2>&1
```
- 404 -> the Stage 1 hand-off hasn't completed yet. Stop and point back to Stage 1; do not proceed.
- 200 -> update the guide's repo URL references (frontmatter `fork repo link`, any `git clone` commands, "Related Resources"/"Additional Reading" links) from `<your-github-user>/sfguide-<id>` to `Snowflake-Labs/sfguide-<id>`, then continue.

**Pre-check 2 -- sfquickstarts fork freshness:**
```bash
cd <sfquickstarts-clone> && git fetch upstream && git log HEAD..upstream/master --oneline | head -1
```
If this shows commits (fork is behind), sync it now (`git checkout master && git pull upstream master`) before Stage 6 branches off it, so the PR branch isn't based on a stale master.

Verify the remaining repos are in place before pushing:

| Repo | Purpose | Expected state |
|------|---------|----------------|
| `Snowflake-Labs/sfguide-<id>` | Companion repo (canonical, direct push) | Exists (confirmed by pre-check 1 above), push access confirmed, pushed to `main` |
| `<your-github-user>/<id>` | Guide staging repo (self-service, no hand-off) | Exists, pushed to `main`, up to date -- Stage 6 sources the sfquickstarts PR content from here |
| `Snowflake-Labs/snowflake-demo-notebooks` | Notebook target | Fork exists at `<your-github-user>/snowflake-demo-notebooks`, synced with upstream |
| `Snowflake-Labs/sfquickstarts` | Guide target | Fork exists at `<your-github-user>/sfquickstarts`, synced with upstream (confirmed by pre-check 2 above) |

**MANDATORY PERMISSION GATE**: Before pushing anything, present this summary to the user:

```
Ready to push to production repos:

  sfquickstarts PR  -> Snowflake-Labs/sfquickstarts (site/sfguides/src/<id>/)
  demo-notebooks PR -> Snowflake-Labs/snowflake-demo-notebooks (<id>/)

This will create public PRs against Snowflake-Labs repos.

Proceed with push? (Yes / No)
```

Do NOT begin Stage 6 until the user explicitly confirms with "Yes", "go ahead", "proceed", or equivalent.
If the user says No or asks to review anything first, stop and wait.

---

### Stage 6: Open the PRs

For each target (skip demo-notebooks if the project has no notebook):

1. In the fork clone, create a branch off the synced upstream default branch (e.g. `git checkout -b add-<id>`).
2. Copy the content in: the guide folder (from `<your-github-user>/<id>`, excluding `_local/`) into `site/sfguides/src/<id>/`, or the notebook into `<id>/`.
3. Commit, push the branch to `<your-github-user>/<fork>`, and open the PR with `gh pr create -R Snowflake-Labs/<repo>`. If a PR for `<id>` already exists, push to its branch instead of opening a new one.

Share both PR links with the user. Restore any git or `gh auth` settings changed for this stage.

---

## Stopping Points

- Setup: paths collected, `<id>` derived, repos checked/created
- Verification: sfguide-verify completed all 4 stages
- Stage 1: hand-off requested, confirmed complete before continuing
- Stage 2: clarity suggestions approved
- Stage 3: architecture diagram decision made
- Stage 4: humanized text approved
- Pre-review: servers stopped, ZIP rebuilt, reviewer notes shared
- Stage 5: repos confirmed, explicit go-ahead received
- Stage 6: both PRs created, links shared with user

## Output

- Two open PRs: one to `Snowflake-Labs/sfquickstarts`, one to `Snowflake-Labs/snowflake-demo-notebooks`
- Companion source repo at `Snowflake-Labs/sfguide-<id>` up to date
- Guide staging repo at `<your-github-user>/<id>` up to date
- A clean, verified, human-sounding guide that matches the live project
