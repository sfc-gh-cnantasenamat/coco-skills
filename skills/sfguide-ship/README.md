# SFGuide Ship

A Cortex Code skill that takes a Snowflake developer guide (sfguide/quickstart) and its companion repo from "drafted" to open PRs in `Snowflake-Labs`.

## How it works

1. **Verification:** runs `sfguide-verify` (readiness audit, end-to-end test, sync check, fixes).
2. **Hand-off:** drafts the request to move the companion repo into `Snowflake-Labs`.
3. **Polish:** clarity audit, architecture diagram check, and a humanizing pass.
4. **Pre-review checkpoint:** stops local servers, rebuilds the ZIP, and drafts notes for reviewers.
5. **Publish:** confirms the repos and forks, asks for explicit approval, then opens PRs to `Snowflake-Labs/sfquickstarts` and `Snowflake-Labs/snowflake-demo-notebooks`.

Nothing is pushed to `Snowflake-Labs` without your explicit go-ahead.

## Usage

```
$sfguide-ship Ship my sfguide at ~/guides/my-guide
```

Requires the [GitHub CLI](https://cli.github.com/) authenticated with an account that has forks of `sfquickstarts` and `snowflake-demo-notebooks`. Install `sfguide-verify` alongside this skill.

## Author

Chanin Nantasenamat, Snowflake
