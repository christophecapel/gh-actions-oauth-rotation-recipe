# Changelog

All notable changes to this recipe.

Format: each release under a version heading. Anti-chronological (newest first).

---

## [Unreleased]

### Planned — v0.2: Google Health API support

The Fitbit Web API (the recipe's origin incident) is migrating to the [Google Health API](https://developers.google.com/health/migration) on Google OAuth 2.0, with the legacy API turned down September 2026. Google OAuth 2.0 uses a different refresh model from the single-use providers this recipe targets today, so v0.2 will add a tested Google Health / Google OAuth 2.0 path — built and verified against a live integration, not a drop-in rename. Targeted for after the new API stabilises (Google advises against launching integrations before end of May 2026 while breaking changes land).

---

## [v0.1.0] — 2026-05-27

### Initial release

A drop-in recipe for GitHub Actions workflows that consume single-use OAuth refresh tokens. Works today for Strava, Whoop, Oura, Spotify, and other single-use-rotation providers. Built from a real 3-day production blackout (2026-05-08 → 2026-05-10) where a transient GitHub push 500 + a structurally non-functional fallback path took down a Fitbit pipeline.

**What's in the initial release:**

- `.github/workflows/rotation.yml` — workflow yaml with `GH_PAT` wiring + 3-attempt push retry pattern
- `scripts/refresh_token.py` — provider-agnostic OAuth refresh + atomic persistence + secret update + rotation invariant log line + abort-on-persistence-failure
- `scripts/update_secret.py` — pynacl-encrypted GitHub Actions secret update helper with 3-attempt retry
- `docs/failure-modes.md` — three concrete failure modes from the real incident
- `docs/adoption.md` — env var checklist, provider-specific gotchas (Strava, Spotify, Whoop, Oura) + Fitbit→Google Health migration note
- `tests/test_refresh.py` — 10 unit tests covering happy path, abort-on-file-failure, abort-on-api-failure, fallback path, secret update
- `.github/workflows/tests.yml` — CI matrix (Python 3.9, 3.10, 3.11, 3.12) + workflow yaml syntax validation

**License:** MIT. **Companion to:** [`claude-mechanisms` #9 Atomic credential persistence](https://github.com/christophecapel/claude-mechanisms/blob/main/mechanisms/09-atomic-credential-persistence.md).
