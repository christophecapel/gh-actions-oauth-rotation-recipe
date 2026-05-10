#!/usr/bin/env python3
"""
update_secret.py

Update a GitHub Actions secret via the REST API. Encrypts the value with the
repo's public key (pynacl SealedBox), then PUTs the encrypted blob.

Used by refresh_token.py to keep the refresh-token secret in sync with the
rotated value on every workflow run. Without this, the secret-as-fallback
recovery path (described in docs/failure-modes.md) is non-functional.

Required env vars:
    GH_PAT              fine-grained PAT with `secrets:write` scope on the target repo
    GITHUB_REPOSITORY   owner/repo (auto-set in GitHub Actions; set manually for local runs)

CLI usage:
    python3 scripts/update_secret.py <SECRET_NAME> <SECRET_VALUE>

As a module:
    from scripts.update_secret import update_github_secret
    success = update_github_secret("MY_TOKEN", "abc123")
"""

import base64
import os
import sys
import time

import requests

try:
    from nacl import public as _nacl_public
    _PYNACL_AVAILABLE = True
except ImportError:
    _PYNACL_AVAILABLE = False


def _encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypt a secret value with the repo's public key (GitHub Secrets API requirement)."""
    if not _PYNACL_AVAILABLE:
        raise ImportError("pynacl required. Install with: pip install pynacl")
    public_key_bytes = base64.b64decode(public_key_b64)
    box = _nacl_public.SealedBox(_nacl_public.PublicKey(public_key_bytes))
    encrypted = box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def update_github_secret(name: str, value: str, repo: str = None, gh_pat: str = None) -> bool:
    """Overwrite a GitHub Actions secret via the API. Returns True on success.

    Retries 3 times with exponential backoff (2s, 4s, 8s). If all retries fail,
    returns False. Caller is responsible for ensuring the value is also
    persisted somewhere else (e.g. a token file) so the next run can recover.

    Args:
        name:   Secret name (e.g. "OAUTH_REFRESH_TOKEN")
        value:  The plaintext secret value
        repo:   "owner/repo" (defaults to GITHUB_REPOSITORY env var)
        gh_pat: GitHub PAT with secrets:write scope (defaults to GH_PAT env var)
    """
    gh_pat = gh_pat or os.environ.get("GH_PAT")
    if not gh_pat:
        print(f"[secret-update] WARNING: GH_PAT not set — skipping secret update for {name}.")
        print("[secret-update] WARNING: the secret-as-fallback recovery path is now non-functional.")
        print("[secret-update] WARNING: see docs/failure-modes.md for why this matters.")
        return False

    repo = repo or os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print(f"[secret-update] WARNING: GITHUB_REPOSITORY not set — cannot update secret {name}.")
        return False

    headers = {
        "Authorization": f"Bearer {gh_pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for attempt in range(1, 4):
        try:
            key_resp = requests.get(
                f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
                headers=headers,
                timeout=10,
            )
            if key_resp.status_code != 200:
                raise ValueError(f"public key fetch failed: {key_resp.status_code}")

            key_data = key_resp.json()
            encrypted = _encrypt_secret(key_data["key"], value)

            put_resp = requests.put(
                f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
                headers=headers,
                json={"encrypted_value": encrypted, "key_id": key_data["key_id"]},
                timeout=10,
            )
            if put_resp.status_code in (201, 204):
                print(f"[secret-update] GitHub secret {name} updated successfully.")
                return True
            raise ValueError(f"secret update failed: {put_resp.status_code} {put_resp.text[:100]}")

        except Exception as exc:
            if attempt < 3:
                backoff = 2 ** attempt
                print(f"[secret-update] WARNING: attempt {attempt}/3 failed: {exc} — retrying in {backoff}s")
                time.sleep(backoff)
            else:
                print(f"[secret-update] WARNING: GitHub secret {name} update failed after 3 attempts: {exc}")
                output_file = os.environ.get("GITHUB_OUTPUT")
                if output_file:
                    try:
                        with open(output_file, "a") as _f:
                            _f.write("secret_update_failed=true\n")
                    except OSError:
                        pass

    return False


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("usage: python3 scripts/update_secret.py <SECRET_NAME> <SECRET_VALUE>", file=sys.stderr)
        return 2

    name, value = argv
    ok = update_github_secret(name, value)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
