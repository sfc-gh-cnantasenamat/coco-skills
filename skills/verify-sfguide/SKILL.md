---
name: verify-sfguide
id: verify-sfguide
title: Verify a Snowflake Guide
summary: Audit, test end to end, and sync-check a Snowflake developer guide and its companion repo before shipping.
description: "Verify and fix an sfguide (quickstart) before shipping: readiness audit, end-to-end verification, guide-project sync check, and blocker fixes. Use standalone to check guide quality during development, or as a delegate from ship-sfguide. Triggers: verify sfguide, audit sfguide, check sfguide, validate quickstart, sfguide readiness check, is my sfguide ready, check my guide. Do NOT use for writing a new guide from scratch or for general markdown proofreading."
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
  - snowflake_sql_execute
prompt: "Verify my sfguide at ~/guides/my-guide before I ship it"
language: en
---

# Verify SF Guide

## Purpose

Quality-gate workflow for an sfguide and its companion project. Runs four sequential stages: readiness audit, end-to-end verification, guide-project sync check, and blocker fixes. Works standalone or as a delegate from `ship-sfguide`.

Placeholders used below:
- `<your-github-user>`: the GitHub account that hosts the companion repo before it moves to `Snowflake-Labs`
- `<test-connection>`: a Snowflake connection to a test or demo account, not a production account

---

## Setup

Ask user:
```
To start the verification checklist, please provide:
1. Path to the sfguide folder (containing <id>/<id>.md and assets/)
2. Path to the companion project/notebook (if separate from the guide folder)
3. Your GitHub user (where the companion repo lives before hand-off)
4. A Snowflake connection name for a test account, for live tests
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

If the companion project path does not exist, report it as missing and stop.

If the sfguide folder/file does not exist, stop and ask the user to create the guide first (or provide the correct path).

**Derive `<id>` from the guide's frontmatter** (the `id:` field in `<id>/<id>.md`). This is the single naming key used for the rest of the workflow. If the folder name and frontmatter `id` disagree, flag it now and resolve it before continuing.

**Check whether the companion repo exists on GitHub:**
```bash
gh api repos/<your-github-user>/sfguide-<id> --jq '.html_url' 2>&1
```

If it doesn't exist yet, create it now so there's somewhere to push fixes to in Stage 4.

---

## Workflow

### Stage 1: Publish-Readiness Audit

Check every item below. Report PASS/FAIL for each; collect all failures before moving on.

**Frontmatter:**
- [ ] `status: Published`
- [ ] `id` matches the `.md` filename (without `.md`) AND the parent folder name
- [ ] `author`, `summary`, `categories`, `feedback link` all present
- [ ] `categories` includes at least `snowflake-site:taxonomy/solution-center/certification/quickstart`

**Structure:**
- [ ] `<id>/<id>.md` exists
- [ ] `<id>/assets/` folder exists -- if it does not exist AND there are no `![](assets/...)` image references in the guide, auto-create the empty folder (`mkdir assets/`) and note it as a convention fix rather than a blocker. If images are referenced but the folder is missing, that is a blocker.
- [ ] No internal docs in `assets/` (e.g. `CLI.md`, `KNOWN_ISSUES.md`, `screenshot.md`) -- move these to a local `_local/` folder outside the submission folder

**Asset integrity:**
- [ ] Every `![](assets/...)` reference in the `.md` resolves to an existing file
- [ ] No unused images in `assets/` that are never referenced in the guide

**URLs:**
- [ ] Repo URL check -- **state-aware**:
  - If `Snowflake-Labs/sfguide-<id>` does not exist yet: a `github.com/<your-github-user>/sfguide-<id>` URL is *expected* and does **not** fail this check.
  - If `Snowflake-Labs/sfguide-<id>` exists: every repo URL must point to `Snowflake-Labs/sfguide-<id>`. Any personal account URL is a hard blocker. Report every occurrence with its line number.
- [ ] No placeholder/TODO/FIXME text remaining

**Formatting:**
- [ ] No headers deeper than H4 (`####`)
- [ ] No HTML in markdown (causes render errors)
- [ ] Em/en dashes: run `grep -n '[—–]' <id>.md` and report the count and line numbers. Each occurrence is a failure; rewrite using commas, parentheses, or separate sentences in Stage 4.

**STOP**: Present full PASS/FAIL report. Wait for user to acknowledge before Stage 2.

---

### Stage 2: End-to-End Verification

Walk through every step in the guide as if you are a first-time reader with a clean environment.

For each step:
- Confirm the command/action produces the expected output described in the guide
- Confirm any screenshots or diagrams match the current state of the app or UI
- Flag any step that assumes context not yet established, is missing, or is out of order

**Path coverage:** list every way the guide says the project can run or deploy (local, Streamlit Community Cloud, Streamlit in Snowflake, etc.). Each path needs explicit steps, any setup script it relies on must exist in the companion repo, and objects created anywhere in the guide must be removed in a top-level `## Clean Up` step (not buried in another section). A missing path, script, or cleanup step is a blocker.

**Live Snowflake test:** run the guide's setup SQL/script end to end on `<test-connection>`. Check row counts and that the app actually renders, then drop every object you created. If the SQL tool can't target `<test-connection>`, use the Python connector (`snowflake.connector.connect(connection_name='<test-connection>')`). Flag any command that only works from a CLI (e.g. `PUT` fails in a Snowsight worksheet) and make sure the guide says so and lists the CLI in prerequisites. If a path can't be tested with the real tool the reader uses (e.g. the Snowflake CLI isn't installed), say so in the findings.

**Screenshots:** capture at 100% browser zoom, one per scene the step describes, and recapture any image whose UI or code changed since it was taken.

Produce a numbered list of issues found (or "No issues -- all steps verified").

**STOP**: Present verification findings. Wait for acknowledgement.

---

### Stage 3: Guide <-> Project Sync Check

Check against the **live public repo** (what readers actually clone), not just local files. Use the companion repo's current URL (`<your-github-user>/sfguide-<id>` pre-hand-off, `Snowflake-Labs/sfguide-<id>` post-hand-off) to fetch the raw files directly from GitHub:

```bash
# Example: fetch key config files from the live repo
curl -s https://raw.githubusercontent.com/<owner>/sfguide-<id>/main/snowflake.yml
curl -s https://raw.githubusercontent.com/<owner>/sfguide-<id>/main/config.py
# repeat for any other config/settings files
```

**Config file scan -- personal resource names:**
Compare every resource name in config files (`snowflake.yml`, `config.py`, `*.toml`, `*.env`, connection helpers, etc.) against the names the guide tells the reader to create in the Setup SQL. Flag any mismatch -- these cause silent deploy failures for readers who followed the guide exactly.

Common culprits:
- `snowflake.yml`: `database`, `query_warehouse`, `compute_pool`, `external_access_integrations`
- `config.py` or equivalent: stage FQNs, database/schema/warehouse constants
- Any hardcoded personal identifiers (account names, usernames, personal DB/schema names)

**Code block sync:**
- All code snippets in the guide match the live repo exactly (no stale function names, renamed variables, or old SQL)
- File names, env var names, warehouse/database/schema names are consistent between guide and live repo

**Number consistency:** every timing, count, or other figure must match across guide prose, tables, the companion README, and any text baked into images (hero/before-after diagrams are easy to miss -- open them and read them). Flag each mismatch with its location.

**README parity:** the companion README should mirror the guide's run, deploy, and clean-up sections, and its file table should list every tracked file (`git ls-files`).

**Missing guide steps:**
- If any config file requires editing before the project will work (e.g. `snowflake.yml` must be updated to match the reader's resource names), confirm the guide has an explicit step telling the reader to do so. If it doesn't, that is a blocker.

Produce a numbered list of discrepancies with the specific file, line, and mismatched value (or "In sync -- no mismatches found").

**STOP**: Present sync findings. Wait for acknowledgement.

---

### Stage 4: Fix All Blockers

Fix everything flagged in Stages 1-3:

1. Move any internal docs out of `assets/` into `_local/`
2. Push code/sync fixes to `<your-github-user>/sfguide-<id>` (the companion repo)
3. Apply all code/sync fixes to the guide so it matches the project
4. Fix any broken steps, outdated snippets, formatting violations, or placeholder text

**STOP**: Summarize all changes made. Confirm with user.

---

## Stopping Points

- Setup: paths collected, `<id>` derived, companion repo checked/created
- Stage 1: readiness report acknowledged
- Stage 2: verification findings acknowledged
- Stage 3: sync findings acknowledged
- Stage 4: fixes applied and confirmed

## Output

A verified, consistent sfguide with all mechanical blockers resolved. The companion repo at `<your-github-user>/sfguide-<id>` is up to date and in sync with the guide.
