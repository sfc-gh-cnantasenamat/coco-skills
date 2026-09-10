---
name: streamlit-add-chat-page
title: Add Chat Page to Streamlit
summary: Build a Cortex Analyst chat page for a Streamlit-in-Snowflake app — semantic view, fuzzy literal resolution, and a robust chat UI.
description: |
  Build a natural-language 'chat with your data' page for a Streamlit-in-Snowflake
  (SiS) app, powered by Cortex Analyst over a semantic view. Covers the semantic
  layer (flattened base view + semantic view with named metrics + Cortex Search
  literal resolution) and the chat UI (Analyst REST call, multi-turn history,
  results/answer expanders, empty-result handling, feedback logging, and a
  regression harness). Includes a robustness checklist and general-vs-niche
  edge-case guidance.

  Use when: adding a chat or conversational-analytics page to a SiS app, building a
  Cortex Analyst UI, or letting users ask questions about a table/dashboard in plain
  English.

  Triggers: cortex analyst chat, chat page, chat with your data, streamlit chat
  snowflake, conversational analytics, natural language query page, text-to-sql app,
  ask questions about data, add chat to streamlit.

  Do NOT use for: free-form document Q&A / RAG over unstructured text (use Cortex
  Search with an agent), or a single fixed dashboard chart (just write the SQL).
prompt: Add a Cortex Analyst chat page to my Streamlit-in-Snowflake app.
language: en
status: Published
author: Chanin Nantasenamat, Lead Developer Advocate, OSS
type: snowflake
tools:
  - snowflake_sql_execute
  - Bash
  - Read
  - Write
  - Edit
---

# Cortex Analyst Chat Page (Streamlit in Snowflake)

Build a "chat with your data" page: the user asks in plain English, **Cortex
Analyst** turns it into SQL against a **semantic view**, the page runs it and
shows results + a short natural-language answer. Two parts: a **semantic layer**
(server-side) and a **chat page** (app code).

Templates: `references/semantic_layer.sql`, `references/chat_page.py`, `references/eval_harness.py`.

## When to use
- Adding a chat / NL-query page to an existing SiS dashboard or data app.
- Exposing a table, view, or metric set to non-analysts conversationally.

## When NOT to use
- Free-form document Q&A / RAG over unstructured text → use Cortex Search (agent), not Analyst.
- A fixed dashboard chart → just write the SQL; a chat page is overkill.

## Workflow

### Step 1 — Model the semantic layer
1. **Flatten to ONE view.** Do all joins and pre-derive any parsed/computed
   columns (regex splits, flags, per-row composites) in a single SQL view. This
   keeps the semantic view **single-table**: no relationships to model, and Analyst
   is far more reliable. It also doubles as a pre-aggregated rollup that speeds up
   the rest of the app. **Mind the grain:** you own the join, so a one-to-many join
   will duplicate rows and inflate `SUM`/`AVG`/`COUNT` — keep the join at the intended
   grain (or pre-aggregate the many side) and count entities with `COUNT(DISTINCT)`.
2. **Create the semantic view** over that one view (`CREATE SEMANTIC VIEW`):
   - **Dimensions** = categorical/filter columns; **metrics** = aggregates.
   - **Encode derived/composite metrics as NAMED metrics** (e.g. a ratio-of-averages
     score) so the LLM uses your exact formula and can never mis-derive it.
   - Add `WITH SYNONYMS` + `COMMENT` to every table/dimension/metric — this is
     what Analyst reads to map natural language to columns.
3. **Seed accuracy controls** (biggest levers, cheap):
   - **Verified queries** (`AI_VERIFIED_QUERIES`): a handful of question→SQL pairs,
     ideally reusing your existing dashboard queries. This anchors generation on
     known-good patterns and is the #1 accuracy lever.
   - **`AI_SQL_GENERATION`**: embed domain rules (use named metrics, case-insensitive
     filters, sensible defaults) so the model doesn't reinvent them.
4. **⚠️ STOP** — show the DDL and get approval before deploying.

### Step 2 — Fix literal resolution with Cortex Search (the big accuracy win)
Snowflake string `=` is **case-sensitive**. Analyst will emit
`WHERE category = 'cortex search'` for a stored value of `Cortex Search` → **zero
rows, no answer**. Fix it structurally:
- **High-cardinality string dimensions (>10 distinct values):** attach a **Cortex
  Search service** (`WITH CORTEX SEARCH SERVICE <fqn> USING <col>`). Analyst then
  fuzzy-resolves the user's phrase to the canonical stored value before writing SQL.
  This also fixes wording/typo/abbreviation mismatches, not just case.
- **Low-cardinality (1-10):** provide sample values instead (no service needed).
- Do this for every user-facing filter column (categories, model/product names, …).

### Step 3 — Build the chat page (`pages/chat.py`)
Adapt `references/chat_page.py`. It implements:
- **Analyst REST call:** in SiS use `_snowflake.send_snow_api_request("POST",
  "/api/v2/cortex/analyst/message", {}, {}, body, None, 60000)` with
  `body = {"messages": [...], "semantic_view": "<fqn>"}`; connector-token fallback for local dev.
- **Multi-turn:** accumulate `messages` (user + analyst turns) and resend the full
  history each call so follow-ups ("what about baseline?") keep context.
- **Run the returned SQL directly** — it is already fully qualified; do NOT pass it
  through any bare-name qualifier (double-qualification → "object does not exist").
- **Answer narrative:** summarize the result via `AI_COMPLETE(<flash-model>, ...)`
  (fast/cheap) with a deterministic fallback; feed the last ~10 turns for context.
- **UX:** Generated SQL / Results / Answer expanders; example-question buttons via a
  `pending_q` + `st.rerun()` handoff; empty-result path lists valid values.
- **Guardrails:** execute **SELECT/WITH only**; cap rendered rows (`MAX_ROWS`); render
  Analyst **warnings** and **clarification/suggestions** (no SQL) as guidance, not errors.
- **Feedback loop:** 👍/👎 buttons + a `CHAT_FEEDBACK` table logging question, generated
  SQL, request_id, and status — mine it later for new verified queries and accuracy tracking.

### Step 4 — Deploy, verify, guard against regressions
- Deploy the app (SiS runs **owner's rights**, so the app's owner role must have
  access to the semantic view + Cortex).
- Verify the model BEFORE trusting the UI:
  `cortex analyst query "<real question>" --view <fqn>` and confirm the generated
  SQL uses the **canonical literal** (e.g. `'Cortex Search'`, not `'cortex search'`).
- Keep a **gold-question regression harness** (`references/eval_harness.py`) and rerun it
  after any semantic-view change to catch questions that silently stop working.
- **⚠️ STOP** — confirm end-to-end before finishing.

## Robustness checklist
- [ ] Named metrics for every computed value (no formulas left to the LLM).
- [ ] View grain verified — no one-to-many fan-out; entity counts use `COUNT(DISTINCT)`.
- [ ] NULLs COALESCE'd on filter/group dimensions; ratio metrics guard div-by-zero (`NULLIF`).
- [ ] Synonyms + comments on all dimensions/metrics.
- [ ] Cortex Search on high-cardinality string dims; sample values on low-cardinality.
- [ ] A few verified queries seeded (reuse existing dashboard SQL).
- [ ] `AI_SQL_GENERATION` domain rules set.
- [ ] SELECT-only execution + row cap + query safety.
- [ ] Warnings + clarification (no-SQL) responses handled gracefully.
- [ ] Empty-result path lists valid values.
- [ ] Feedback logging in place.
- [ ] Gold-question eval harness passes before/after changes.

## Edge cases: general vs niche
**Universal (handled by the templates — apply to any dataset):**
- Grain / fan-out double-counting; NULL dimensions & metrics; divide-by-zero; case/literal
  mismatch; out-of-scope questions; large results; summary-prompt input treated as untrusted.

**Data-shape-dependent (handle if your data has that shape):**
- Time-series/trends → add a real date dimension + a line chart (the template's chart
  heuristic only does bars).
- Over-fuzzy Cortex Search matches → tighten dimension descriptions / cardinality.
- Ambiguous synonyms (two metrics both "score") → disambiguate names/synonyms.
- Non-English questions → have the summary model answer in the question's language.

**Niche (don't re-teach — model with the semantic-view `patterns` skill):**
- Period-over-period (YoY/MoM/SPLY), rolling/YTD windows, fiscal calendars.
- Non-additive snapshot facts (balances, headcount — must not sum over time).
- SCD2 / as-of temporal joins, multi-fact / role-playing dimensions, unit conversions, geospatial.


## Gotchas (hard-won)
- **`AI_COMPLETE`, not `SNOWFLAKE.CORTEX.COMPLETE`** — the latter is deprecated / gated.
- **Per-item `COMMENT` needs `=`**: `COMMENT = '...'` (bare `COMMENT '...'` is a syntax error).
- **Dimension clause order is fixed:** `expr → WITH SYNONYMS → COMMENT → WITH CORTEX
  SEARCH SERVICE` (the search-service clause must come **last**).
- **Fully-qualify the search-service name** (`DB.SCHEMA.NAME`) in the semantic view.
- **Search services have a `TARGET_LAG`** (e.g. 24h): new values become *fuzzy*-matchable
  after refresh; exact matches always work immediately.
- **Compute-then-render** the assistant turn once (don't render inline during the
  API calls) so the live path and the redraw-on-rerun path stay identical.
- **`RESULT_SCAN` / session state** don't survive across pooled connections — verify
  DDL by re-querying the object, not by trusting a prior `SHOW`/`LAST_QUERY_ID`.

## Stopping points
- ✋ Step 1: approve semantic-view DDL before deploy.
- ✋ Step 4: confirm the NL round-trip works before calling it done.

## Output
A deployed SiS chat page backed by: a flattened base view, a single-table semantic
view with named metrics + synonyms, and Cortex Search services on string dimensions.
