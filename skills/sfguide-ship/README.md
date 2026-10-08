# SFGuide Ship

Prepare and publish an existing guide using this order:

1. Resolve guide paths and actual optional companion repository locations.
2. Polish content locally and approve technical changes.
3. Obtain approval for any companion publication/transfer and finalize URLs.
4. Verify the final content with `sfguide-verify`.
5. Build the ZIP and check it and the staged submission against the verified hashes.
6. Approve and open/update only applicable PRs; do not merge automatically.

```text
$sfguide-ship Prepare ~/guides/my-guide/my-guide.md for publishing
```

Install `sfguide-verify` and its declared dependencies first. The GitHub CLI is needed for GitHub operations; repository names and default branches are discovered, not assumed. No companion or notebook is required for guide-only submissions. No remote writes occur without authorization, including to personal staging repositories.

Reports remain local. Failed or applicable UNTESTED checks block release. Any post-verification edit requires revalidation and a new package. See the verification package's `references/workflow-contract.md` for the shared CLI and limitations.

## Author

Chanin Nantasenamat, Snowflake