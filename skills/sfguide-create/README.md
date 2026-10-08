# SFGuide Create

A Cortex Code skill that converts a notebook, app, or document into a Snowflake developer guide and packages it for review.

## How it works

1. Collect the guide author, source path, optional companion repository, and category preferences.
2. Map the source into the guide's sections and confirm the outline.
3. Generate the guide while preserving source code and technical content.
4. Use the shared validator to check metadata and assets, review links and disclosure, then deliver markdown, a DRAFT ZIP, and a local handoff report. Execution remains UNTESTED.

Snowflake Feature categories are off by default. A companion repository link is included only when supplied. The skill does not publish the guide, execute source code, or open a PR.

## Usage

```text
$sfguide-create Create a guide from ~/projects/my-project/tutorial.ipynb
```

Provide a readable notebook, app, or document. Notebook sources require a dedicated notebook reader; PDF and Word sources require a reader supporting those formats. URL verification uses available web tools and the GitHub CLI for GitHub links. Unavailable checks are reported explicitly.

Install `sfguide-verify` and its declared Python dependencies for shared validation and packaging. Resolve its installed location via skill discovery; sibling directories are not required. The shared contract is in that package's `references/workflow-contract.md`. Optional images and companion projects remain optional throughout the handoff. Reports stay outside the distributable ZIP.

## Related

- [sfguide-verify](../sfguide-verify/README.md) checks the guide against the working project.
- [sfguide-ship](../sfguide-ship/README.md) handles review and approval-gated publishing.

## Author

Chanin Nantasenamat, Snowflake