#!/usr/bin/env bash
# The docs-lint `links` check: lychee on a built site, with the rules in lychee.toml.
# Usage: check-links.sh <site>   (build first: cd tinyml && uv run mkdocs build)
# Uses $LYCHEE if set, else `lychee` on PATH.
set -euo pipefail
site=$1
repo=$(cd "$(dirname "$0")/../.." && pwd)
site_url="https://willyowl.github.io/docs-guardian/" # site_url in tinyml/mkdocs.yml

# Links to the site's own URL are checked against this build, not the live site.
"${LYCHEE:-lychee}" --config "$repo/lychee.toml" \
  --remap "^${site_url//./\\.} file://$(cd "$site" && pwd)/" \
  "$site"
