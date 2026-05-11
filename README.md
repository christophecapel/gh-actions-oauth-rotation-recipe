![Banner](banner.png)

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

> A drop-in recipe for GitHub Actions workflows that consume single-use OAuth refresh tokens.

Built from a real 3-day production blackout. Most OAuth-in-Actions tutorials stop at "here's how to use a token" and don't cover single-use rotation, push retry, or fallback instrumentation. This recipe addresses all three.

## What's in the box

| File | What it does |
|---|---|
| `.github/workflows/rotation.yml` | Workflow yaml with the full pattern: refresh → persist → secret update → do work → commit + push with retry |
| `scripts/refresh_token.py` | Provider-agnostic OAuth refresh + atomic persistence to all sinks (file + secret) |
| `scripts/update_secret.py` | GitHub Actions secret update helper using pynacl (the easy-to-skip "fallback" wiring) |
| `docs/failure-modes.md` | What breaks if you don't do this — three concrete failure modes from a real incident |
| `docs/adoption.md` | How to add this to your repo — env vars, secrets, provider-specific gotchas |
| `tests/test_refresh.py` | Tests covering the happy path, the abort-on-persistence-failure path, and the fallback path |

## When to use this

You need this recipe if **all** of these apply:

1. You're running a GitHub Actions workflow that consumes an OAuth API (Fitbit, Strava, Whoop, Oura, Spotify, Notion, Hubspot, etc.)
2. The API provider issues **single-use refresh tokens** with rotation (most modern providers do)
3. You want the workflow to keep running unattended for weeks or months

If your API uses long-lived static tokens, you don't need this. If your access tokens last days, you don't need this. The recipe earns its keep when:

- Refresh tokens are single-use and rotate on every exchange
- The chain can break silently if any rotation is lost
- You can't afford to babysit the integration

## Quick start

Three steps:

1. **Copy the files** (`.github/workflows/rotation.yml`, `scripts/refresh_token.py`, `scripts/update_secret.py`) into your repo
2. **Set five secrets** in your repo's Actions settings (see `docs/adoption.md`)
3. **Adapt the workflow yaml**: change `git config user.email`, replace the "Do work" placeholder step with your actual API calls

Full walkthrough in `docs/adoption.md`.

## Why this recipe exists

> 7 weeks of green workflow runs. Then a single transient `Internal Server Error` on a `git push` lost a freshly-rotated refresh token. The runner discarded its filesystem; the repo stayed at the previous (now-consumed) token. Three days of dead-token-cascade followed. Worse: the script had a "fallback to GitHub secret" recovery path written. It required `GH_PAT` in the env. The workflow yaml had never piped `GH_PAT` in. The fallback had been silently no-op since the day it was added.

Three failure modes, all real, all in `docs/failure-modes.md`:

1. **Single-use refresh tokens** + ephemeral GitHub Actions runners = chain breaks if any rotation isn't pushed back to the repo
2. **Transient GitHub push 500s** lose freshly-rotated tokens unless you retry the push
3. **Recovery paths that have never fired** silently no-op for months and don't help when you finally need them

The recipe addresses all three with concrete code.

## Companion project

This recipe is the implementation of the [Atomic credential persistence](https://github.com/christophecapel/claude-mechanisms/blob/main/mechanisms/09-atomic-credential-persistence.md) mechanism applied to GitHub Actions workflows.

## Contributing

See `CONTRIBUTING.md`. Bug reports + provider-specific gotchas welcome.

## License

MIT.
