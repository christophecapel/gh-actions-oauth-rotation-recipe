#!/usr/bin/env bash
#
# install.sh -- scaffold the OAuth rotation recipe into a target repo.
#
# Copies the three mandatory files (workflow + two scripts) and the two
# recommended files (CI + tests) into a target git repo, creating directories
# as needed. Never overwrites an existing file unless --force is passed.
#
# Usage:
#   ./install.sh [TARGET_DIR] [--with-tests] [--force]
#
#   TARGET_DIR     Repo to install into (default: current directory)
#   --with-tests   Also copy tests/ + the CI workflow
#   --force        Overwrite files that already exist (default: skip + warn)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="."
WITH_TESTS=0
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --with-tests) WITH_TESTS=1 ;;
    --force)      FORCE=1 ;;
    -*)           echo "Unknown flag: $arg" >&2; exit 2 ;;
    *)            TARGET="$arg" ;;
  esac
done

if [ ! -d "$TARGET" ]; then
  echo "Target directory does not exist: $TARGET" >&2
  exit 1
fi

MANDATORY=(
  ".github/workflows/rotation.yml"
  "scripts/refresh_token.py"
  "scripts/update_secret.py"
)
RECOMMENDED=(
  ".github/workflows/tests.yml"
  "tests/test_refresh.py"
  "tests/__init__.py"
)

copy_one() {
  local rel="$1"
  local src="$SCRIPT_DIR/$rel"
  local dst="$TARGET/$rel"
  if [ ! -f "$src" ]; then
    echo "  skip (not in recipe): $rel" >&2
    return
  fi
  if [ -f "$dst" ] && [ "$FORCE" -eq 0 ]; then
    echo "  exists, skipping (use --force): $rel"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "  installed: $rel"
}

echo "Installing OAuth rotation recipe into: $TARGET"
for f in "${MANDATORY[@]}"; do copy_one "$f"; done
if [ "$WITH_TESTS" -eq 1 ]; then
  for f in "${RECOMMENDED[@]}"; do copy_one "$f"; done
fi

cat <<'NEXT'

Next steps (see docs/adoption.md for the full walkthrough):
  1. Set five repo secrets: OAUTH_TOKEN_URL, OAUTH_CLIENT_ID,
     OAUTH_CLIENT_SECRET, OAUTH_REFRESH_TOKEN, and GH_PAT.
     GH_PAT is REQUIRED, not optional -- without it the secret-as-fallback
     recovery path silently no-ops.
  2. Edit .github/workflows/rotation.yml: set git user.email, adjust the
     schedule, and replace the "Do work" placeholder with your API calls.
  3. Trigger the workflow manually and confirm the rotation invariant line:
     [refresh] Rotation invariant: file_persisted=True secret_updated=True

Done.
NEXT
