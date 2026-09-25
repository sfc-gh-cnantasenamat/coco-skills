---
name: handoff
description: "Summarize the current session into a structured handoff brief for resuming work in a new session. Use when: handing off context, starting a new session, session summary, continuing work, resume session, hand off, handoff, new context window, context transfer, wrap up session, session brief."
---

# Session Handoff

Produces a structured handoff document from the current session so a new session can resume work without re-establishing context.

## Workflow

### Step 1: Scan the Session

Review the entire conversation from the beginning. Collect:

- **Primary goal**: What the user came here to accomplish
- **Work completed**: Specific tasks finished, files created/edited, queries run, decisions made
- **Current state**: Where things stand right now -- what is working, what is partially done
- **Key decisions**: Any architectural, design, or approach choices made and their reasoning
- **Blockers / open questions**: Anything unresolved, waiting on, or uncertain
- **Next actions**: The concrete next steps the work was heading toward
- **Artifacts**: File paths, table names, stage paths, repo URLs, branch names, workspace URIs, or other pointers a new session will need
- **Environment**: Snowflake account, connection name, database/schema/warehouse context, active role, working directory if relevant

Do NOT summarize conversation turns. Extract facts and state, not dialogue.

### Step 2: Draft the Handoff Brief

Format the brief as a self-contained markdown block the user can paste at the top of a new chat. Use this structure:

~~~
## Session Handoff

### Goal
[One or two sentences: what this session was trying to accomplish]

### Completed
- [Specific thing done]
- [Another thing done]

### Current State
[Where things stand -- what is working, what is partial, what was last touched]

### Key Decisions
- [Decision + reason, e.g. "Chose dynamic table over task+stream because refresh lag was acceptable"]

### Blockers / Open Questions
- [Anything unresolved or that needs input]

### Next Steps
1. [Most immediate next action]
2. [Following action]
3. [Further steps]

### Context & Artifacts
- **Working dir**: `<path>`
- **Snowflake account**: `<account>`
- **Database / Schema**: `<db.schema>`
- **Key files**: `<path>`, `<path>`
- **Key objects**: `<TABLE>`, `<STAGE>`, `<VIEW>`
- **Branch / PR**: `<branch>` / `<url>` (if applicable)
- **Other**: [anything else a new session needs to pick up where this left off]
~~~

Omit any section that has nothing to put in it. Do not pad with filler.

### Step 3: Present the Brief

Output the handoff brief in a fenced markdown code block so the user can copy it cleanly with one click.

Follow with a short note (one sentence) on anything the new session will need to do first that is not obvious from the brief -- e.g., reloading a skill, reconnecting to a service, or re-reading a particular file.

### Step 4: Offer Memory Save (optional)

If the session contains decisions or constraints that are non-obvious and durable (apply to future unrelated sessions), offer:

> "There are [N] facts here worth saving to memory so future sessions pick them up automatically. Want me to save them?"

Only offer if such facts exist. Do not save automatically. If the user accepts, use `cortex memory remember` for each fact.

### Step 5: Launch New Session

After presenting the brief (and handling any memory save), ask:

> "Want me to open a new session with this handoff as the starting context?"

If the user agrees:

1. Write the brief content to `/tmp/coco-handoff.md` (plain text, no fenced code block wrapper)
2. Launch a new session:
   ```bash
   cortex --goal "$(cat /tmp/coco-handoff.md)" &
   ```
3. Tell the user: "New session launched with the handoff as its opening goal."

The `&` runs it in the background so this session stays alive. The new session will open as a separate window and immediately begin working from the handoff context.

## Stopping Points

- After Step 3 -- user decides whether to save to memory and/or launch a new session

## Output

A fenced code block with the handoff brief, an optional memory-save, and an optional new session launch.
