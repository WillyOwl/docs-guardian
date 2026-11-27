#!/usr/bin/env bash
# The docs-lint `links` check: lychee on a built site, with the rules in lychee.toml.
# Usage: check-links.sh <site>   (build first: cd tinyml && uv run mkdocs build)
# Uses $LYCHEE if set, else `lychee` on PATH.
set -euo pipefail
site=$1
repo=$(cd "$(dirname "$0")/../.." && pwd)
site_url="https://willyowl.github.io/docs-guardian/" # site_url in tinyml/mkdocs.yml
site_dir=$(cd "$site" && pwd)

# Root-relative links (/docs-guardian/...) resolve as on the deployed site: in a
# web root that serves this build under the site URL's path.
web_root=$(mktemp -d)
trap 'rm -rf "$web_root"' EXIT
mount="$web_root/${site_url#https://*/}"
mkdir -p "$(dirname "$mount")"
ln -s "$site_dir" "${mount%/}"

# Links to the site's own URL are checked against this build, not the live site.
"${LYCHEE:-lychee}" --config "$repo/lychee.toml" \
  --remap "^${site_url//./\\.} file://$site_dir/" \
  --root-dir "$web_root" \
  "$site"
