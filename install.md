# Installation

Two ways to add the recipe to your repo. Both end at the same place: the workflow + scripts in your tree, five secrets set, the rotation invariant line in your logs.

## Option 1: scaffold script (one command)

Clone the recipe and run the installer against your target repo:

```bash
git clone https://github.com/christophecapel/gh-actions-oauth-rotation-recipe.git
cd gh-actions-oauth-rotation-recipe
./install.sh /path/to/your-repo            # mandatory files only
./install.sh /path/to/your-repo --with-tests   # also copy CI + tests
```

The installer copies the three mandatory files (`.github/workflows/rotation.yml`, `scripts/refresh_token.py`, `scripts/update_secret.py`) plus, with `--with-tests`, the CI workflow and test suite. It creates directories as needed and never overwrites an existing file unless you pass `--force`.

## Option 2: manual copy

Copy these into your repo by hand:

```
.github/workflows/rotation.yml   # adapt to your work step + schedule
scripts/refresh_token.py         # generic, no changes needed
scripts/update_secret.py         # generic, no changes needed
```

Recommended (avoid silent regressions):

```
.github/workflows/tests.yml
tests/test_refresh.py
tests/__init__.py
```

## After either option

1. **Set five repo secrets** (`Settings → Secrets and variables → Actions`): `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_REFRESH_TOKEN`, `GH_PAT`. `GH_PAT` is REQUIRED, not optional: without it the secret-as-fallback recovery path silently no-ops.
2. **Adapt `rotation.yml`**: set `git config user.email`, adjust the schedule, replace the "Do work" placeholder with your API calls.
3. **First run**: trigger manually and confirm `[refresh] Rotation invariant: file_persisted=True secret_updated=True`.

Full walkthrough, secret-by-secret, with provider gotchas: [`docs/adoption.md`](docs/adoption.md).

> **Starting a new Fitbit integration?** Read the Fitbit migration note in `docs/adoption.md` first: the Fitbit Web API is moving to the Google Health API (legacy turndown September 2026). See the [roadmap](README.md#roadmap) for the planned Google Health variant.
