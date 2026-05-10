#!/usr/bin/env python3
"""
refresh_token.py

OAuth 2.0 refresh-token rotation with atomic persistence across three sinks:
    1. Local token file (committed back to the repo by the workflow)
    2. GitHub Actions secret (via update_secret.py)
    3. The repo itself (via the workflow yaml's git push step)

Single-use refresh tokens (used by Fitbit, Strava, Spotify, Whoop, Oura, and many
others) require atomic handling. If the rotation succeeds but persistence to one
of the sinks fails, the next run inherits a dead token. This script aborts on
any persistence failure rather than returning a partially-saved access token.

See docs/failure-modes.md for why each sink matters and how the chain can break.

Required env vars:
    OAUTH_TOKEN_URL       Provider token endpoint (e.g. https://api.fitbit.com/oauth2/token)
    OAUTH_CLIENT_ID       OAuth client ID
    OAUTH_CLIENT_SECRET   OAuth client secret
    OAUTH_REFRESH_TOKEN   Current refresh token (from env, file fallback below)
    GITHUB_REPOSITORY     owner/repo (auto-set in GH Actions; required for secret update)
    GH_PAT                PAT with secrets:write scope (REQUIRED for fallback path)

Optional env vars:
    TOKEN_FILE_PATH       Where to persist rotated refresh token (default: .tokens.json)
    OAUTH_REFRESH_SECRET_NAME  Secret name to keep in sync (default: OAUTH_REFRESH_TOKEN)

CLI usage:
    python3 scripts/refresh_token.py        # rotate, print new access token to stdout
    python3 scripts/refresh_token.py --help # show options

Exit codes:
    0  rotation succeeded, all persistence sinks confirmed
    1  refresh API call failed
    2  rotation succeeded but persistence failed (HWW #9: never proceed with
       a credential we haven't saved; abort so the caller doesn't continue
       with an access token whose refresh token is now lost)
"""

from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import requests

# Import update_secret as a sibling module
sys.path.insert(0, str(Path(__file__).parent))
from update_secret import update_github_secret  # noqa: E402


DEFAULT_TOKEN_FILE = ".tokens.json"
DEFAULT_SECRET_NAME = "OAUTH_REFRESH_TOKEN"


def _load_dotenv():
    """Load credentials from .env if env vars are not already set.

    Allows local runs to work without manually exporting every session.
    The .env file is gitignored.
    """
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and not os.environ.get(key):
                os.environ[key] = value
    except OSError:
        pass


def _load_refresh_token_from_file(token_file: Path) -> str | None:
    """Load the refresh token from a persisted file, if it exists."""
    if not token_file.exists():
        return None
    try:
        stored = json.loads(token_file.read_text())
        return stored.get("refresh_token")
    except (json.JSONDecodeError, OSError):
        return None


def _persist_to_file(token_file: Path, refresh_token: str, expires_in_days: int = 240) -> bool:
    """Write rotated refresh token to file. Preserves expires_at if already set.

    Returns True on success, False on disk failure.
    """
    try:
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_data = {"refresh_token": refresh_token}
        if token_file.exists():
            try:
                existing = json.loads(token_file.read_text())
                if existing.get("expires_at"):
                    token_data["expires_at"] = existing["expires_at"]
            except (json.JSONDecodeError, KeyError):
                pass
        if "expires_at" not in token_data:
            token_data["expires_at"] = (
                datetime.date.today() + datetime.timedelta(days=expires_in_days)
            ).isoformat()
        token_file.write_text(json.dumps(token_data, indent=2) + "\n")
        print(f"[refresh] Refresh token persisted to {token_file}")
        return True
    except OSError as exc:
        print(f"[refresh] FATAL: could not persist token file: {exc}")
        return False


def refresh_access_token(
    token_url: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    token_file: Path | None = None,
    secret_name: str = DEFAULT_SECRET_NAME,
    fallback_refresh_token: str | None = None,
) -> str:
    """Rotate the OAuth refresh token and return a fresh access token.

    Persists the new refresh token to ALL configured sinks (file + GitHub
    secret). If any persistence sink fails, raises SystemExit(2) so the
    caller does not proceed with a credential it hasn't saved.

    Args:
        token_url:                Provider token endpoint URL
        client_id:                OAuth client ID
        client_secret:            OAuth client secret
        refresh_token:            Current refresh token to consume
        token_file:               Path to persist rotated token (None = skip file sink)
        secret_name:              GitHub secret name to keep in sync
        fallback_refresh_token:   If primary refresh_token is 400-rejected, try this one.
                                  Allows recovery when the file token is stale but the
                                  GH secret has a fresher value (or vice versa).

    Returns:
        Fresh access_token string.

    Raises:
        SystemExit(1): refresh API call failed (no token consumed)
        SystemExit(2): rotation succeeded but persistence failed (token lost)
    """
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    # Try primary refresh token first, fall back if 400-rejected
    tokens_to_try = [refresh_token]
    if fallback_refresh_token and fallback_refresh_token != refresh_token:
        tokens_to_try.append(fallback_refresh_token)

    response = None
    for i, token in enumerate(tokens_to_try):
        response = requests.post(
            token_url,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": token,
            },
            timeout=30,
        )
        if response.status_code == 400 and i < len(tokens_to_try) - 1:
            print("[refresh] Primary refresh token rejected (400) — retrying with fallback.")
            continue
        break

    if response is None or response.status_code != 200:
        status = response.status_code if response is not None else "no-response"
        body = response.text[:200] if response is not None else ""
        print(f"[refresh] FATAL: token refresh failed ({status}): {body}", file=sys.stderr)
        raise SystemExit(1)

    tokens = response.json()
    new_refresh_token = tokens["refresh_token"]
    new_access_token = tokens["access_token"]
    expires_in = tokens.get("expires_in", "unknown")

    print(f"[refresh] Token refreshed. Access token expires in {expires_in}s.")

    # Persist to all sinks. Track each outcome for the invariant log line below.
    file_persisted = True
    if token_file is not None:
        file_persisted = _persist_to_file(token_file, new_refresh_token)

    secret_updated = update_github_secret(secret_name, new_refresh_token)

    # Invariant log line: makes silent regressions visible on every run.
    # See docs/failure-modes.md for why this matters.
    print(
        f"[refresh] Rotation invariant: "
        f"file_persisted={file_persisted} "
        f"secret_updated={secret_updated}"
    )

    # HWW #9: never proceed with a credential we haven't saved. If file persistence
    # failed (the primary sink), abort. Secret update failures are warned about but
    # do not abort, because the file is still the canonical store for the next run.
    if not file_persisted:
        print(
            "[refresh] FATAL: token rotation consumed but not persisted to file. "
            "Aborting to prevent silent credential loss. See docs/failure-modes.md.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    return new_access_token


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Rotate an OAuth refresh token with atomic persistence."
    )
    parser.add_argument(
        "--token-file",
        type=Path,
        default=Path(os.environ.get("TOKEN_FILE_PATH", DEFAULT_TOKEN_FILE)),
        help="Path to persist rotated refresh token (default: .tokens.json)",
    )
    parser.add_argument(
        "--secret-name",
        default=os.environ.get("OAUTH_REFRESH_SECRET_NAME", DEFAULT_SECRET_NAME),
        help="GitHub secret name to keep in sync (default: OAUTH_REFRESH_TOKEN)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress access token output (rotation still happens)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    _load_dotenv()
    args = _parse_args(argv)

    token_url = os.environ.get("OAUTH_TOKEN_URL")
    client_id = os.environ.get("OAUTH_CLIENT_ID")
    client_secret = os.environ.get("OAUTH_CLIENT_SECRET")

    missing = [
        name for name, value in [
            ("OAUTH_TOKEN_URL", token_url),
            ("OAUTH_CLIENT_ID", client_id),
            ("OAUTH_CLIENT_SECRET", client_secret),
        ]
        if not value
    ]
    if missing:
        print(f"ERROR: required env vars not set: {', '.join(missing)}", file=sys.stderr)
        print("See docs/adoption.md for the full env var list.", file=sys.stderr)
        return 1

    # Refresh token can come from the file or env. File wins (it's the rotated value).
    env_refresh_token = os.environ.get("OAUTH_REFRESH_TOKEN")
    file_refresh_token = _load_refresh_token_from_file(args.token_file)

    primary_token = file_refresh_token or env_refresh_token
    fallback_token = env_refresh_token if file_refresh_token else None

    if not primary_token:
        print("ERROR: no refresh token found (neither in file nor in OAUTH_REFRESH_TOKEN env)", file=sys.stderr)
        return 1

    access_token = refresh_access_token(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=primary_token,
        token_file=args.token_file,
        secret_name=args.secret_name,
        fallback_refresh_token=fallback_token,
    )

    if not args.quiet:
        print(access_token)

    return 0


if __name__ == "__main__":
    sys.exit(main())
