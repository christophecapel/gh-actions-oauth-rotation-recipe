# Contributing

Thanks for thinking about contributing.

## What this repo is

A self-contained recipe for GitHub Actions workflows that consume single-use OAuth refresh tokens. The scope is intentionally narrow: token rotation, atomic persistence, push retry, fallback instrumentation. It is not a full OAuth library and is not trying to become one.

## What kinds of contributions are welcome

- **Bug reports** with a minimum reproduction (env vars set, command run, expected vs actual output)
- **Provider-specific gotchas** for `docs/adoption.md` (e.g. Spotify quirks, Whoop OAuth scopes, Strava endpoint differences)
- **Test cases** that cover an actual failure mode you hit and would like protected against regression
- **Documentation improvements** especially around `docs/failure-modes.md` and `docs/adoption.md`

## What is out of scope

- New OAuth providers as built-in adapters. The recipe is provider-agnostic by design; adoption guides for specific providers live in `docs/adoption.md`.
- Features unrelated to refresh-token rotation (token storage backends, encryption schemes, monitoring integrations).
- Anything that requires breaking the workflow yaml's shape without a strong reason.

## How to file an issue

Include:

1. The provider you are using (Fitbit / Spotify / Strava / etc.)
2. The relevant log lines from the failed workflow run (especially the rotation invariant line if you have one)
3. What you expected to happen
4. What actually happened

## How to file a PR

1. Open an issue first if the change is non-trivial. Avoids wasted work on something out of scope.
2. Tests stay green: `python3 -m unittest tests -v`
3. New behavior gets a new test. Test names describe the behavior, not the implementation.
4. CHANGELOG.md gets an entry under `## [Unreleased]`.
5. No em dashes in markdown (repo convention).

## Cadence

This is a small recipe maintained alongside other work. Expect responses in days, not hours. Critical security issues get faster attention if flagged as such.
