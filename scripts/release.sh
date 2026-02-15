#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Monorepo Release Script
# Bumps version across all packages using git-cliff + git tags
# Usage: ./scripts/release.sh
# ============================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# --- 1. Determine current version from git tags ---
HAS_TAGS=true
if git describe --tags --abbrev=0 > /dev/null 2>&1; then
    CURRENT_TAG=$(git describe --tags --abbrev=0)
    CURRENT_VERSION=${CURRENT_TAG#v}
else
    HAS_TAGS=false
    CURRENT_VERSION="0.0.0"
    echo "No existing tags found. This will be the initial release."
fi

echo "Current version: v${CURRENT_VERSION}"

# --- 2. Compute bumped version via git-cliff ---
BUMPED_VERSION=$(uvx git-cliff --bumped-version)
PLAIN_VERSION=${BUMPED_VERSION#v}

# Skip same-version check only when tags already exist
# (first release always proceeds even if bumped == initial)
if [ "$HAS_TAGS" = "true" ] && [ "$PLAIN_VERSION" = "$CURRENT_VERSION" ]; then
    echo "No version bump needed. No unreleased conventional commits found."
    exit 0
fi

echo "Target version: ${BUMPED_VERSION} (plain: ${PLAIN_VERSION})"

# --- 3. Generate CHANGELOG.md and RELEASE.md at root ---
uvx git-cliff --strip header --tag "$BUMPED_VERSION" -o CHANGELOG.md
uvx git-cliff --latest --strip header --tag "$BUMPED_VERSION" --unreleased -o RELEASE.md

echo "Generated CHANGELOG.md and RELEASE.md"

# --- 4. Update backend pyproject.toml version ---
sed -i "s/^version = \".*\"/version = \"${PLAIN_VERSION}\"/" saegim-backend/pyproject.toml
echo "Updated saegim-backend/pyproject.toml to ${PLAIN_VERSION}"

# --- 5. Update frontend package.json version ---
jq --arg v "$PLAIN_VERSION" '.version = $v' saegim-frontend/package.json > saegim-frontend/package.json.tmp \
    && mv saegim-frontend/package.json.tmp saegim-frontend/package.json
echo "Updated saegim-frontend/package.json to ${PLAIN_VERSION}"

# --- 6. Update e2e package.json version ---
jq --arg v "$PLAIN_VERSION" '.version = $v' e2e/package.json > e2e/package.json.tmp \
    && mv e2e/package.json.tmp e2e/package.json
echo "Updated e2e/package.json to ${PLAIN_VERSION}"

# --- 7. Sync backend lock file ---
(cd saegim-backend && uv lock)
echo "Synced saegim-backend/uv.lock"

# --- 8. Stage all changed files ---
git add CHANGELOG.md RELEASE.md
git add saegim-backend/pyproject.toml saegim-backend/uv.lock
git add saegim-frontend/package.json
git add e2e/package.json

# --- 9. Commit, push, tag, push tags ---
git commit -m "chore(release): bump version to ${PLAIN_VERSION}"
git push origin

git tag -a "$BUMPED_VERSION" -m "Release ${BUMPED_VERSION}"
git push origin --tags

echo "Released version ${BUMPED_VERSION} successfully!"
