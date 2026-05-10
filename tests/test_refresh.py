"""
Tests for refresh_token.py + update_secret.py.

Run with: python3 -m unittest tests.test_refresh -v
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Make scripts/ importable
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import refresh_token  # noqa: E402
import update_secret  # noqa: E402


class TestRefreshHappyPath(unittest.TestCase):
    """End-to-end rotation succeeds: API returns 200, file persists, secret updates."""

    def setUp(self):
        self.tmp_file = REPO_ROOT / "tests" / ".test-tokens.json"
        if self.tmp_file.exists():
            self.tmp_file.unlink()

    def tearDown(self):
        if self.tmp_file.exists():
            self.tmp_file.unlink()

    @patch("refresh_token.update_github_secret")
    @patch("refresh_token.requests.post")
    def test_happy_path_returns_access_token_and_persists(self, mock_post, mock_secret):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token-abc",
            "refresh_token": "new-refresh-token-xyz",
            "expires_in": 28800,
        }
        mock_post.return_value = mock_response
        mock_secret.return_value = True

        access_token = refresh_token.refresh_access_token(
            token_url="https://example.com/oauth/token",
            client_id="cid",
            client_secret="csecret",
            refresh_token="old-refresh-token",
            token_file=self.tmp_file,
            secret_name="MY_TOKEN",
        )

        self.assertEqual(access_token, "new-access-token-abc")
        self.assertTrue(self.tmp_file.exists())
        stored = json.loads(self.tmp_file.read_text())
        self.assertEqual(stored["refresh_token"], "new-refresh-token-xyz")
        self.assertIn("expires_at", stored)
        mock_secret.assert_called_once_with("MY_TOKEN", "new-refresh-token-xyz")


class TestRefreshAbortsWhenFilePersistenceFails(unittest.TestCase):
    """HWW #9: never return an access token whose refresh token wasn't saved."""

    @patch("refresh_token._persist_to_file")
    @patch("refresh_token.update_github_secret")
    @patch("refresh_token.requests.post")
    def test_systemexit_2_when_file_write_fails(self, mock_post, mock_secret, mock_persist):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "would-be-leaked-access-token",
            "refresh_token": "lost-refresh-token",
            "expires_in": 28800,
        }
        mock_post.return_value = mock_response
        mock_persist.return_value = False  # file write failed
        mock_secret.return_value = True

        with self.assertRaises(SystemExit) as ctx:
            refresh_token.refresh_access_token(
                token_url="https://example.com/oauth/token",
                client_id="cid",
                client_secret="csecret",
                refresh_token="old-refresh-token",
                token_file=Path("/tmp/should-not-be-written.json"),
            )
        self.assertEqual(ctx.exception.code, 2)


class TestRefreshAbortsWhenApiFails(unittest.TestCase):
    """Refresh API non-200: no token consumed, exit 1."""

    @patch("refresh_token.requests.post")
    def test_systemexit_1_when_token_endpoint_returns_400(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant"
        mock_post.return_value = mock_response

        with self.assertRaises(SystemExit) as ctx:
            refresh_token.refresh_access_token(
                token_url="https://example.com/oauth/token",
                client_id="cid",
                client_secret="csecret",
                refresh_token="already-consumed-token",
            )
        self.assertEqual(ctx.exception.code, 1)


class TestFallbackRefreshTokenPath(unittest.TestCase):
    """Primary token rejected 400 → falls back to secondary token."""

    @patch("refresh_token.update_github_secret")
    @patch("refresh_token.requests.post")
    def test_fallback_used_when_primary_400s(self, mock_post, mock_secret):
        # First call returns 400, second returns 200
        first = MagicMock(status_code=400, text="invalid_grant")
        second = MagicMock(status_code=200)
        second.json.return_value = {
            "access_token": "access-via-fallback",
            "refresh_token": "fresh-from-fallback",
            "expires_in": 28800,
        }
        mock_post.side_effect = [first, second]
        mock_secret.return_value = True

        with patch("refresh_token._persist_to_file", return_value=True):
            access_token = refresh_token.refresh_access_token(
                token_url="https://example.com/oauth/token",
                client_id="cid",
                client_secret="csecret",
                refresh_token="stale-file-token",
                fallback_refresh_token="fresh-secret-token",
                token_file=Path("/tmp/should-be-mocked.json"),
            )

        self.assertEqual(access_token, "access-via-fallback")
        self.assertEqual(mock_post.call_count, 2)
        # The fresh token from the SECOND call's response is what gets persisted
        mock_secret.assert_called_once_with("OAUTH_REFRESH_TOKEN", "fresh-from-fallback")


class TestUpdateSecretSkipsWithoutGhPat(unittest.TestCase):
    """Without GH_PAT, secret update returns False (graceful no-op + loud warning)."""

    def test_returns_false_when_gh_pat_missing(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}, clear=True):
            result = update_secret.update_github_secret("MY_TOKEN", "value", gh_pat=None)
        self.assertFalse(result)

    def test_returns_false_when_repo_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            result = update_secret.update_github_secret("MY_TOKEN", "value", gh_pat="fake-pat")
        self.assertFalse(result)


class TestUpdateSecretSuccess(unittest.TestCase):
    """Happy path: public key fetch + encrypt + PUT all succeed."""

    @patch("update_secret._encrypt_secret")
    @patch("update_secret.requests")
    def test_returns_true_on_201(self, mock_requests, mock_encrypt):
        mock_requests.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"key": "fake-public-key-b64", "key_id": "fake-key-id"},
        )
        mock_encrypt.return_value = "encrypted-blob"
        mock_requests.put.return_value = MagicMock(status_code=201)

        result = update_secret.update_github_secret(
            "MY_TOKEN", "value", repo="owner/repo", gh_pat="fake-pat"
        )
        self.assertTrue(result)

    @patch("update_secret._encrypt_secret")
    @patch("update_secret.requests")
    def test_returns_true_on_204(self, mock_requests, mock_encrypt):
        mock_requests.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"key": "k", "key_id": "kid"},
        )
        mock_encrypt.return_value = "blob"
        mock_requests.put.return_value = MagicMock(status_code=204)

        result = update_secret.update_github_secret(
            "MY_TOKEN", "value", repo="owner/repo", gh_pat="fake-pat"
        )
        self.assertTrue(result)


class TestModuleLoad(unittest.TestCase):
    """Sanity: modules import + key functions exist."""

    def test_refresh_token_module_loads(self):
        self.assertTrue(callable(refresh_token.refresh_access_token))
        self.assertTrue(callable(refresh_token.main))

    def test_update_secret_module_loads(self):
        self.assertTrue(callable(update_secret.update_github_secret))
        self.assertTrue(callable(update_secret.main))


if __name__ == "__main__":
    unittest.main()
