#!/usr/bin/env bash
# Post the Drift Report as one pull request comment, or rewrite the earlier one.
# Usage: post-drift-report.sh <report.md>, with GH_TOKEN, GITHUB_REPOSITORY, PR and
# GITHUB_RUN_ID set (drift-check.yml sets them).
#
# Advisory (ADR 0001): a GitHub API failure (a fork's read-only token, an outage)
# only warns, and the report stays in the job summary.
set -euo pipefail
report=$1
warn() { echo "::warning::$1; the report is in the job summary. GitHub said: $2"; }

# The report's hidden first line carries the marker and the counts.
first_line=$(head -n 1 "$report")
marker=${first_line%% changes=*}
changes=$(sed -E 's/.* changes=([0-9]+).*/\1/' <<< "$first_line")

# GitHub caps a comment at 65536 characters.
limit=60000
if [ "$(wc -c < "$report")" -gt "$limit" ]; then
  head -c "$limit" "$report" > body.md
  printf '\n\n…truncated: the full report is in the job summary of run %s.\n' \
    "$GITHUB_RUN_ID" >> body.md
else
  cp "$report" body.md
fi

# Only this workflow's own comment counts, never a person's that happens to match.
# Every id is read, then the first kept: piping into `head` could kill gh with SIGPIPE.
if ! ids=$(gh api "repos/$GITHUB_REPOSITORY/issues/$PR/comments" --paginate \
  --jq ".[] | select(.user.login == \"github-actions[bot]\")
             | select(.body | startswith(\"$marker\")) | .id" 2> lookup-error.txt); then
  warn "Could not look for an earlier Drift Report" "$(cat lookup-error.txt)"
  exit 0
fi
existing=${ids%%$'\n'*}
if [ -n "$existing" ]; then
  action="rewrite comment $existing"
  cmd=(gh api -X PATCH "repos/$GITHUB_REPOSITORY/issues/comments/$existing" -F body=@body.md)
elif [ "$changes" != "0" ]; then
  action="post a new comment"
  cmd=(gh api -X POST "repos/$GITHUB_REPOSITORY/issues/$PR/comments" -F body=@body.md)
else
  echo "No API Changes and no earlier Drift Report: nothing to post."
  exit 0
fi

if error=$("${cmd[@]}" 2>&1 > /dev/null); then
  echo "Drift Report: did $action."
else
  warn "Could not $action" "$error"
fi
