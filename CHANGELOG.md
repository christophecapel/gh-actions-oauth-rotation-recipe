# Changelog

All notable changes to this recipe.

Format: each release under a version heading. Anti-chronological (newest first).

---

## [v0.1.0] — 2026-05-19

### Initial release

A drop-in recipe for GitHub Actions workflows that consume single-use OAuth refresh tokens. Built from a real 3-day production blackout (2026-05-08 → 2026-05-10) where a transient GitHub push 500 + a structurally non-functional fallback path took down a Fitbit pipeline.

**What's in the initial release:**

- `.github/workflows/rotation.yml` — workflow yaml with `GH_PAT` wiring + 3-attempt push retry pattern
- `scripts/refresh_token.py` — provider-agnostic OAuth refresh + atomic persistence + secret update + rotation invariant log line + abort-on-persistence-failure
- `scripts/update_secret.py` — pynacl-encrypted GitHub Actions secret update helper with 3-attempt retry
- `docs/failure-modes.md` — three concrete failure modes from the real incident
- `docs/adoption.md` — env var checklist, provider-specific gotchas (Fitbit, Strava, Spotify, Whoop, Oura)
- `tests/test_refresh.py` — 10 unit tests covering happy path, abort-on-file-failure, abort-on-api-failure, fallback path, secret update
- `.github/workflows/tests.yml` — CI matrix (Python 3.9, 3.10, 3.11, 3.12) + workflow yaml syntax validation

**License:** MIT. **Companion to:** [`claude-mechanisms` #9 Atomic credential persistence](https://github.com/christophecapel/claude-mechanisms/blob/main/mechanisms/09-atomic-credential-persistence.md).
