# humanizing

> Edit AI-generated prose so it reads like a specific person wrote it, not like a language model.

## What it does

The skill detects and removes common AI-voice patterns — hedge stacking, hollow openers, generic intensifiers, list-of-three padding, mirror-back phrasing, and other tells — then rewrites the prose to sound like the author's natural voice. It applies automatically to any generated prose (blog posts, docs, emails, proposals) and can also be invoked explicitly for an edit pass.

## Usage

Invoke with `$humanizing` or let Cortex Code activate it automatically when you say something like:

```
Humanize this draft.
Make this sound less like AI.
Do an edit pass on this blog post.
Does this sound AI-written?
```

## Patterns detected

| Pattern | Example |
|---|---|
| Hedge stacking | "It's important to note that..." |
| Hollow openers | "Great question!" |
| Generic intensifiers | "This is a really powerful approach" |
| Mirror-back | Restating the user's question before answering |
| List-of-three padding | Adding a third item just for rhythm |
| Colon-before-list | "Here are the key benefits:" |
| Summary recap | Restating everything at the end |

## Scope

- **Applies to**: blog posts, docs, bios, proposals, social posts, emails, summaries, chat responses
- **Does NOT apply to**: code, code comments, SQL, commit messages, or other non-prose technical output

## Requirements

- No external dependencies. Works with any Cortex Code session.

## Author

Chanin Nantasenamat

## License

Apache 2.0 — see [LICENSE](LICENSE).
