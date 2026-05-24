# Failure modes

This recipe exists because of three failure modes that most OAuth-in-Actions tutorials don't cover. If you only know about the happy path, your token chain WILL break — usually weeks after you stop watching it.

## 1. The single-use refresh token trap

Most OAuth providers (Fitbit, Strava, Whoop, Oura, and many others) implement refresh tokens as **single-use** with rotation. Every time you exchange a refresh token for a new access token, the provider invalidates the old refresh token and gives you a new one. If you don't persist the new one before the next run, the old one is permanently dead.

**Why this bites in GitHub Actions:**

GitHub Actions runners are ephemeral. Any file written during a run is lost when the runner shuts down, unless you commit + push it back to your repo. So the rotation needs to happen, AND the new token needs to land in your repo, AND the push needs to succeed — all before the runner dies.

**How this recipe addresses it:**

- `scripts/refresh_token.py` persists the new refresh token to a local file inside the repo on every rotation
- The workflow's commit + push step pushes the file back to the repo
- The next run reads the file before doing anything else

## 2. The transient push 500

GitHub's push endpoint occasionally returns `Internal Server Error`. It's rare but real. If your workflow rotates a single-use token and then the push fails, the runner dies holding the only copy of the new token. Next run inherits the previous (now-consumed) token, gets a 400 from the provider, and the chain is dead.

**What happens without retry:**

The author's Fitbit integration ran for nine weeks of green workflow runs. Then on 2026-05-08, the workflow rotated the token (smoke + main, consuming 2 single-use tokens), got `remote: Internal Server Error` on push, and lost both fresh tokens. The next three days inherited a dead token and the workflow failed every day until the chain was manually reset by re-authentication.

**How this recipe addresses it:**

`.github/workflows/rotation.yml` wraps the `git pull --rebase + git push` in a 3-attempt retry loop with exponential backoff (0s, 8s, 24s). A single transient 500 no longer breaks the chain.

## 3. The fallback that was never tested

The most insidious failure mode. You write a recovery path. It looks correct. You ship it. Months later, when you actually need it, you discover it has been silently disabled since the day it was added — usually because a required env var was never wired into the workflow yaml.

**The concrete example:**

The author's `refresh_token.py` had a "fall back to GitHub secret" recovery path. The logic was: if the file's refresh token is rejected (400), try the value from the `OAUTH_REFRESH_TOKEN` env var (populated from the GitHub secret). The path looked correct in code review.

But the GitHub secret was only useful if it stayed in sync with the rotated value. Keeping it in sync required `update_secret.py` to actually run, which required `GH_PAT` in the workflow's env block. The workflow yaml never piped `GH_PAT` in. So `update_secret.py` had been printing `WARNING: GH_PAT not set — skipping` on every single run, the GitHub secret stayed frozen at whatever value was set during the last manual auth, and the "fallback" was a comment.

When the chain finally broke (failure mode #2 above), the fallback didn't fire because there was no fresher value to fall back to.

**How this recipe addresses it:**

Two things:

1. **The workflow yaml explicitly pipes `GH_PAT` into the rotation step.** Adoption guide flags this as REQUIRED, not optional. If you skip it, you ship a non-functional fallback.

2. **Every rotation prints an invariant log line:** `[refresh] Rotation invariant: file_persisted=<bool> secret_updated=<bool>`. If `secret_updated` is `False` for weeks, the next person reading the logs sees it immediately — not after a 3-day outage.

## Universal lessons

1. **Read the failure logs before theorising.** File mtime, last-success timestamps, anything circumstantial — leave those for second. The first run that failed almost always has the answer in its log.
2. **A fallback you've never tested isn't a fallback.** If your recovery path can no-op silently (skip due to missing config, swallow an exception, etc.), it isn't recovery. Add an invariant log line per critical operation so silent regressions surface on day one, not week 9.
3. **Single-use credentials require atomic handling.** Consume the credential, persist the replacement, verify persistence — in that order. If persistence fails, abort. Don't proceed with work using an access token whose refresh token you just lost.

This recipe is the implementation of the [Atomic credential persistence](https://github.com/christophecapel/claude-mechanisms/blob/main/mechanisms/09-atomic-credential-persistence.md) mechanism applied to GitHub Actions.
