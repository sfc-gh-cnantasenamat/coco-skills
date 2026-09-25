# handoff

> Summarize the current session into a structured handoff brief for resuming work in a new session.

## What it does

The skill scans the full conversation, extracts the primary request, key decisions, files changed, errors encountered, and pending work, then produces a structured handoff document. A new session can pick up where you left off without re-establishing context.

## Usage

Invoke with `$handoff` or let Cortex Code activate it automatically when you say something like:

```
Summarize this session for a handoff.
Wrap up this session so I can continue later.
Create a session brief.
```

## Output sections

| Section | Content |
|---|---|
| Primary Request | What the user asked for and why |
| Key Decisions | Technical choices made during the session |
| Files Changed | Every file created, modified, or deleted |
| Errors & Fixes | Problems hit and how they were resolved |
| Pending Work | Incomplete tasks with clear next steps |
| Snowflake Context | Connection, account, and object details |

## Requirements

- An active Cortex Code session with conversation history.

## Author

Chanin Nantasenamat

## License

Apache 2.0 — see [LICENSE](LICENSE).
