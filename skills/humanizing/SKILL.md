---
name: humanizing
description: "Apply automatically, by default, to every piece of AI-generated prose before delivering it — blog posts, docs, bios, proposals, social posts, emails, summaries, chat responses, any generated natural-language text. Does NOT apply to code, code comments, SQL, commit messages, or other non-prose technical output. Also invoke explicitly when the user asks to humanize, sound more human, sound less like AI, do an edit pass, tighten writing, or remove AI-sounding phrasing. Triggers: humanize this, make this sound human, sound less like AI, edit pass, does this sound AI-written, tighten this up, remove buzzwords, sounds robotic — plus silently on any drafted prose output, without waiting to be asked."
---

# Humanizing

Edit prose so it reads like a specific person wrote it, not like a language model. A pattern below is a **clue**, not proof — human writers use all of these occasionally. The problem is several of them stacking in the same passage, which flattens the writer's actual voice into generic "AI voice."

## When to apply

**Default-on for prose, default-off for code.** Run this pass on any AI-generated natural-language text before it reaches the user: blog posts, articles, bios, proposals, social copy, emails, documentation prose, summaries, and ordinary chat responses that contain more than a sentence or two of narrative writing. Apply it silently as part of drafting, not just when explicitly asked.

Skip it for: code, code comments, docstrings, SQL, config/YAML, commit messages, log output, table/data output, or any other technical artifact where these patterns don't apply and "editing" would just be noise.

## Workflow

### Step 1: Identify the passage

Take the text to edit (pasted content, a file, or something just drafted in this conversation). If it's long, work section by section rather than trying to hold the whole thing in view at once.

### Step 2: Scan for the 8 patterns

For each pattern below: find instances, then cut or rewrite per the fix. Don't just delete — replace with something more specific, since the underlying issue is usually vagueness the pattern was papering over.

| # | Pattern | Tell | Fix |
|---|---------|------|-----|
| 1 | **Empty emphasis** | "That's the whole point." / "Let that sink in." — announces importance instead of earning it | Cut the cue; make the preceding point more specific so it doesn't need a flag |
| 2 | **Manufactured intrigue** | "quietly reshaping," "the quiet part out loud" — inflates an ordinary claim with false drama | State the claim plainly; if it's not actually surprising, don't imply it is |
| 3 | **Staccato drama** | "No roadmap. No guardrails. Just momentum." — fragment stacks with a trailer-like rhythm | Write it as a normal sentence unless the fragmentation is doing real rhythmic work |
| 4 | **Metaphor overload** | Reaching for figurative language by default ("the data whispers") | Revert to a plain statement when the metaphor adds mood but no meaning |
| 5 | **Personification of systems** | "the strategy wakes up," "the market tells us" — giving agency to processes/data | Name the actual actor (a person, a team, a mechanism) |
| 6 | **Simulated reassurance** | "actually," "just" used to sound casual/informal ("you're not actually behind") | Remove the word and check if the claim still holds; if it doesn't add information, cut it |
| 7 | **Inflated description** | "The most underrated statistic in this report..." — superlatives making routine info sound revelatory | Name what the statistic shows and why it matters instead of hyping it |
| 8 | **Performed intimacy** | "Here's the twist that stops you mid-scroll." — predicting the reader's reaction instead of earning it | Let the insight do the work; delete reaction-predicting language entirely |

Also check for, independent of the 8 above:
- **Em dashes and "not X, but Y" constructions** — the two most recognizable AI tells, called out explicitly and repeatedly as something to avoid in narrative prose. Restructure with periods, commas, colons, or separate sentences instead.
- **Corporate/inflated vocabulary** — words like "delve," "leverage," "robust," "seamless," "landscape," "tapestry," "underscore," "testament," "game-changing," "unlock" that show up more in AI output than in how people actually talk. Replace with the plain verb or noun.
- **Vague superlatives without a referent** — "cutting-edge," "state-of-the-art," "world-class" used as filler rather than backed by a specific fact.

### Step 3: Add what only the author could know

The single highest-leverage move, and the one generic AI editing misses: add concrete detail, a number, a specific example, or domain expertise that a generic model wouldn't have. Genuinely human writing is usually distinguishable less by *avoiding* patterns and more by *including* specifics nobody else would think to add. If the draft is thin on specifics, ask for one before finishing the edit rather than papering over the gap with more polished-sounding filler.

### Step 4: Read it aloud (mentally) and compare

After editing, re-read the passage and ask: does this sound like something a person would actually say out loud, in this register? If a phrase still feels like a caption or a trailer voiceover, it's still not fixed.

### Step 5: Show a diff, not just a rewrite

When editing existing text on request, present the edit so the user can see specifically what changed and why (e.g., "cut 'let that sink in' — was empty emphasis" rather than silently swapping in new prose). When applying this pass automatically to freshly drafted prose (Step 0), skip the diff and just deliver the cleaned-up version — there's no prior draft to compare against.

## What NOT to do

- Don't strip out *all* figurative language or informality — the goal is removing the tells that stack up into "AI voice," not producing flat, affectless writing.
- Don't add hedges, disclaimers, or throat-clearing ("It's worth noting that...") — that's its own AI tell.
- Don't over-correct into staccato "punchy" copywriting; that's pattern 3 in a different costume.

## Output

- **On-request edit pass:** the edited passage, plus a short list of what was changed and why (pattern name or rule applied), so the user can spot-check the edits rather than re-reading the whole thing diff-blind.
- **Automatic pass on drafted prose:** just the cleaned-up prose, applied before the response is sent — no need to narrate the edit unless something significant was cut.
