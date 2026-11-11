#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-.}"
SOURCE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$(cd "$TARGET" && pwd)"

# The old root-level boardlib.py shadows the installed BoardLib package.
rm -f "$TARGET/boardlib.py"
mkdir -p "$TARGET/.github/workflows" "$TARGET/tests"
cp "$SOURCE/tracker.py" "$TARGET/tracker.py"
cp "$SOURCE/requirements.txt" "$TARGET/requirements.txt"
cp "$SOURCE/README.md" "$TARGET/README.md"
cp "$SOURCE/.gitignore" "$TARGET/.gitignore"
cp "$SOURCE/.env.example" "$TARGET/.env.example"
cp "$SOURCE/.github/workflows/tracker.yml" "$TARGET/.github/workflows/tracker.yml"
cp "$SOURCE/tests/test_tracker.py" "$TARGET/tests/test_tracker.py"
echo "Updated $TARGET. Review the diff, add the required GitHub Actions secrets, then run the workflow manually."
