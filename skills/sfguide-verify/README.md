# SFGuide Verify

Check a guide and optional companion project without publishing anything. Live tests and technical fixes require authorization; missing checks remain UNTESTED.

```text
$sfguide-verify Verify ~/guides/my-guide/my-guide.md locally
```

The Python 3.10+ helper parses Markdown with markdown-it-py, resolves guide paths, validates metadata and assets, snapshots source files, records evidence, and packages only verified guide content. It performs no network operations or guide execution. Manual attestations record evidence supplied by the caller, not independently verified test results.

See [the shared contract](references/workflow-contract.md) for installation, CLI examples, report states, dependency limitations, and draft/release packaging. All three skills use this implementation. Install this package before using creation or shipping; resolve it by skill discovery rather than assuming sibling directories.

Run regression tests with the dependency-equipped interpreter:

```bash
python -m unittest discover -s "<verify-skill>/tests" -v
```

`sfguide-create` produces a draft and handoff report. `sfguide-ship` finalizes URLs/content, obtains fresh verification, checks ZIP and staged-file equality, and publishes only with approval.

## Author

Chanin Nantasenamat, Snowflake