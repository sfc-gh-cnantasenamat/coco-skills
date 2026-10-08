# SFGuide Verify

A Cortex Code skill that checks a Snowflake developer guide (sfguide/quickstart) and its companion repo before shipping.

## How it works

1. **Readiness audit:** frontmatter, folder structure, image references, repo URLs, and formatting rules.
2. **End-to-end verification:** walks every step as a first-time reader, checks that every run/deploy path has steps and a clean-up step, runs the setup SQL live on a test account, and checks screenshots.
3. **Sync check:** compares the guide against the live companion repo: code blocks, config resource names, numbers (including text inside images), and README parity.
4. **Fix blockers:** applies the fixes and pushes them.

Each stage stops for your acknowledgement before moving on.

## Usage

```
$sfguide-verify Verify my sfguide at ~/guides/my-guide
```

You'll be asked for the guide path, the companion repo path, your GitHub user, and a Snowflake connection to a test account.

## Related

- `sfguide-ship` runs this skill first, then polishes and publishes the guide.

## Author

Chanin Nantasenamat, Snowflake
