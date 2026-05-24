# Adoption guide

How to add this recipe to your own GitHub Actions workflow.

## Prerequisites

- A repo that needs a scheduled GitHub Actions workflow to call an OAuth-protected API
- The API provider issues **single-use refresh tokens** with rotation (true for Fitbit, Strava, Whoop, Oura, Spotify, and many others — check your provider's docs)
- Owner-level access to the repo (you'll need to add secrets and grant `contents: write` to the workflow)

## Step 1 — copy the relevant files into your repo

Three files are mandatory:

```
.github/workflows/rotation.yml   # adapt to your work step + schedule
scripts/refresh_token.py         # generic, no changes needed
scripts/update_secret.py         # generic, no changes needed
```

Two files are recommended (avoid silent regressions):

```
.github/workflows/tests.yml      # CI to keep the scripts working
tests/test_refresh.py            # the test suite
```

## Step 2 — set up secrets in your repo

Go to **Settings → Secrets and variables → Actions** and add five secrets:

| Secret | Value | Required |
|---|---|---|
| `OAUTH_TOKEN_URL` | Provider's token endpoint (e.g. `https://www.strava.com/oauth/token`) | yes |
| `OAUTH_CLIENT_ID` | OAuth client ID from your provider's developer console | yes |
| `OAUTH_CLIENT_SECRET` | OAuth client secret | yes |
| `OAUTH_REFRESH_TOKEN` | Initial refresh token from your one-time OAuth flow | yes |
| `GH_PAT` | Fine-grained PAT with `secrets:write` scope on THIS repo | **REQUIRED, not optional** |

**`GH_PAT` is the most commonly skipped one.** Without it, `update_secret.py` silently no-ops, and the secret-as-fallback recovery path described in `docs/failure-modes.md` becomes non-functional. Don't ship without it.

To create the PAT:

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. **Generate new token**
3. Resource owner: yourself or the org that owns the target repo
4. Repository access: **Only select repositories** → pick the target repo
5. Permissions → Repository permissions → **Secrets: Read and write**
6. Generate, copy the token, paste it into the `GH_PAT` secret on the same repo

## Step 3 — get an initial refresh token

This is provider-specific. You generally need to:

1. Register an OAuth application with the provider (developer console)
2. Run a one-time OAuth flow locally to exchange an authorization code for an access token + refresh token
3. Paste the refresh token into the `OAUTH_REFRESH_TOKEN` secret

Most providers have a quick-start guide for this — for example Strava's developer docs at https://developers.strava.com/docs/authentication/. (Fitbit's legacy guide is at https://dev.fitbit.com/build/reference/web-api/developer-guide/authorization/, but see the Fitbit migration note under provider gotchas before starting a new Fitbit integration.)

After the first workflow run, the recipe takes over the rotation — you won't need to manually update `OAUTH_REFRESH_TOKEN` again unless the chain breaks.

## Step 4 — adapt the workflow yaml

Open `.github/workflows/rotation.yml` and:

1. **Change `git config user.email`** to a bot email under your control
2. **Change the schedule** if `every 6 hours` doesn't match your needs (see https://crontab.guru/)
3. **Replace the "Do work" placeholder step** with your actual API calls using the fresh `$ACCESS_TOKEN`
4. **Decide whether to keep the alert-on-failure step.** It opens a GitHub issue when the workflow fails. Comment it out if you don't want that.

## Step 5 — first run

Trigger the workflow manually (`Actions → OAuth Token Rotation → Run workflow`). On a successful first run you should see:

```
[refresh] Token refreshed. Access token expires in 28800s.
[refresh] Refresh token persisted to .tokens.json
[secret-update] GitHub secret OAUTH_REFRESH_TOKEN updated successfully.
[refresh] Rotation invariant: file_persisted=True secret_updated=True
[push] Succeeded on attempt 1
```

If `secret_updated=False`, `GH_PAT` is missing or misconfigured. Fix before you forget.

If the push step fails 3 times, GitHub is having a bad day. Wait an hour and re-trigger manually — the recipe won't auto-recover because the workflow already exited with the rotation lost. (This is the only remaining failure mode the recipe can't fully prevent. See `docs/failure-modes.md` for the broader context.)

## Provider-specific gotchas

### Fitbit (migrating to Google Health API — read first)

> ⚠️ **The Fitbit Web API is being deprecated.** It is moving to the [Google Health API](https://developers.google.com/health/migration) on Google OAuth 2.0, with the legacy API turned down in **September 2026**. Tokens do not transfer and users must re-consent. If you're starting a new integration, target Google Health, not the legacy endpoint below. Google OAuth 2.0 uses a different refresh model, so a tested Google Health variant of this recipe is on the roadmap (see README). The legacy details below still work until the turndown.

- Access tokens expire in 8 hours. Refresh tokens last ~8 months by default but rotate on every use.
- Token endpoint (legacy): `https://api.fitbit.com/oauth2/token`
- Auth header for token endpoint: `Authorization: Basic <base64(client_id:client_secret)>` (the recipe handles this)

### Strava

- Access tokens expire in 6 hours. Refresh tokens last indefinitely but rotate on use.
- Token endpoint: `https://www.strava.com/oauth/token`
- Auth: `client_id` and `client_secret` in the body, not the header. You'll need to slightly modify `refresh_token.py` for this — open an issue or PR if you need help.

### Spotify

- Access tokens expire in 1 hour.
- Token endpoint: `https://accounts.spotify.com/api/token`
- Refresh tokens generally do NOT rotate (older Spotify behavior) — but the recipe is still useful for the access token lifecycle and the push-retry pattern.

### Whoop, Oura

- Similar to Fitbit pattern. Single-use rotation, Basic auth on token endpoint. Recipe works out of the box.

Open an issue if you adopt the recipe for a provider not listed here and want to add a gotcha section.

## Verifying the chain is healthy

After a few days of automated runs:

1. **Check the workflow run logs** for the rotation invariant line: `file_persisted=True secret_updated=True` should appear on every run
2. **Check the GitHub secret's "Updated" timestamp** — it should match the most recent workflow run, not the date you manually created it
3. **Check `.tokens.json` in your repo** — the file should have a recent commit (one per rotation)

If any of these drift, you have a silent failure brewing. Read the logs of the last successful run vs the most recent run to find the change.
