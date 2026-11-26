#!/usr/bin/env bash
# Captures every check cited for e1f15ea. Run from the scratchpad, which holds:
#   wt (e1f15ea), wt-old (eab5b3c): clean detached worktrees, never modified;
#   mut, mut-old: worktrees at the same commits, where the fixtures are applied.
# Each <name>.txt gets "$ (cd <dir> && cmd)", the output (ANSI stripped) and the exit code.
set -u
S=$(pwd)
EV=$S/ev/e1f15ea
export LYCHEE=$S/lychee/lychee-x86_64-unknown-linux-gnu/lychee NO_MKDOCS_2_WARNING=1
source "$EV/tools/check.sh"
FIX=$EV/fixtures
ONE='git log --oneline -1'
BUILD='(cd tinyml && uv run -q mkdocs build --strict 2>&1 | grep -v "Cache hit\|Copied jupyter\|Converting notebook")'

# Spec 1: the reviewer's valid root-relative link on the real home Page.
check spec1-root-relative-before-fix "$S/mut-old" "$ONE && git apply $FIX/root-relative-actual.patch.git && git diff --stat && $BUILD && bash .github/scripts/check-links.sh tinyml/site"
check spec1-root-relative-fixed "$S/mut" "$ONE && git apply $FIX/root-relative-actual.patch.git && git diff --stat && $BUILD && bash .github/scripts/check-links.sh tinyml/site"
# The same link pointed at a missing Page, and without the /docs-guardian/ prefix: still rejected.
check spec1-root-relative-missing "$S/mut" "$ONE && sed -i 's|(/docs-guardian/quickstart/#quickstart)|(/docs-guardian/missing-page/)|' tinyml/docs/index.md && tail -1 tinyml/docs/index.md && (cd tinyml && uv run -q mkdocs build 2>/dev/null) && bash .github/scripts/check-links.sh tinyml/site"
check spec1-root-relative-unprefixed "$S/mut" "$ONE && sed -i 's|(/docs-guardian/missing-page/)|(/quickstart/)|' tinyml/docs/index.md && tail -1 tinyml/docs/index.md && (cd tinyml && uv run -q mkdocs build 2>/dev/null) && bash .github/scripts/check-links.sh tinyml/site"
(cd "$S/mut" && git checkout -q -- . && rm -rf tinyml/site)

# Red: the new test run against the old script (eab5b3c plus only the e1f15ea test file).
check red-test "$S/mut-old" "git checkout -q -- . && $ONE && git checkout e1f15ea -- tests/test_check_links.py && git status --short && uv run --no-group docs pytest -p no:cacheprovider tests/test_check_links.py -k root_relative"
(cd "$S/mut-old" && git checkout -q eab5b3c -- . && git status --short && rm -rf tinyml/site)

# 404.html: why it was excluded. At eab5b3c without the exclusion, its links can't be resolved.
check 404-before-fix "$S/mut-old" "$ONE && sed -i '/^exclude_path/d' lychee.toml && git diff && (cd tinyml && uv run -q mkdocs build 2>/dev/null) && bash .github/scripts/check-links.sh tinyml/site"
(cd "$S/mut-old" && git checkout -q -- . && rm -rf tinyml/site)

# Fresh checks on the clean e1f15ea worktree.
check check-links-tests "$S/wt" "$ONE && uv run --no-group docs pytest -v -p no:cacheprovider tests/test_check_links.py"
check links "$S/wt" "$ONE && grep -c 404 lychee.toml; (cd tinyml && uv run -q mkdocs build 2>/dev/null) && ls tinyml/site/404.html && bash .github/scripts/check-links.sh tinyml/site"
check strict-build "$S/wt" "$ONE && $BUILD"
check markdownlint "$S/wt" "$ONE && npx --yes markdownlint-cli2@0.24.0"
check vale "$S/wt" "$ONE && $S/vale/vale tinyml/docs"
check pytest-3.14 "$S/wt" "$ONE && uv run --no-group docs python --version && uv run --no-group docs pytest -p no:cacheprovider"
check pytest-3.11 "$S/wt" "$ONE && UV_PROJECT_ENVIRONMENT=$S/env311 uv run -q --python 3.11 --no-group docs python --version && UV_PROJECT_ENVIRONMENT=$S/env311 uv run -q --python 3.11 --no-group docs pytest -p no:cacheprovider"
check ruff "$S/wt" "$ONE && uv run --no-group docs ruff check . && uv run --no-group docs ruff format --check ."
(cd "$S/wt" && rm -rf tinyml/site && git status --short)

# Shorten scratchpad paths.
sed -i "s|$S|<scratchpad>|g; s|$HOME|~|g" "$EV"/*.txt
