#!/usr/bin/env bash
# Check that VERSION matches today's date (local) or the last commit date (CI).
#
# Usage:
#   pre-commit run check-version-date        # local: compares to today
#   CI=1 pre-commit run --all-files          # CI: compares to git log -1 date
set -euo pipefail

if [ -n "${CI:-}" ]; then
  EXPECTED=$(git log -1 --format="%ad" --date=format:"%Y-%m-%d")
else
  EXPECTED=$(date +%Y-%m-%d)
fi

ACTUAL=$(head -1 VERSION 2>/dev/null || echo "")

if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "VERSION (${ACTUAL}) must be ${EXPECTED}"
  exit 1
fi
