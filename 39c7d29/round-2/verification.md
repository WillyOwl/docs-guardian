# Verification steps — PR #11, round 2

Code under review: `39c7d290bbb0a982e8f173d518ea5b03fe23b84c`.
Base: `6af3ec1c790f170e064659a1f23ae2e1f6008c04`.
Capture timestamps are UTC in each raw log. The local date was 2026-11-24
(America/Edmonton). The implementation worktree remained clean throughout.

## Environment and existing checks

In the PR checkout, create separate environments so checks cannot change each
other's dependency sets:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/pr11-review-round2/env314 uv sync --locked --python 3.14 --no-group docs
UV_PROJECT_ENVIRONMENT=/tmp/pr11-review-round2/env311 uv sync --locked --python 3.11 --no-group docs
UV_PROJECT_ENVIRONMENT=/tmp/pr11-review-round2/envdocs uv sync --locked --python 3.14
/tmp/pr11-review-round2/env314/bin/python -m pytest --color=no
/tmp/pr11-review-round2/env311/bin/python -m pytest --color=no
/tmp/pr11-review-round2/env314/bin/ruff check .
/tmp/pr11-review-round2/env314/bin/ruff format --check .
/tmp/pr11-review-round2/env314/bin/docs-guardian snippets tinyml/docs
/tmp/pr11-review-round2/env314/bin/docs-guardian drift --base origin/main --source tinyml/src --docs tinyml/docs
/tmp/pr11-review-round2/envdocs/bin/python -m pytest --nbmake tinyml/docs/notebooks -p no:cacheprovider --color=no
```

The actual Python versions were 3.14.6 and 3.11.15, with pytest 9.2.0, ruff
0.17.6, and nbmake 1.5.5. Dependencies came from this commit's `uv.lock`.
The notebook command used temporary JUPYTER_CONFIG_DIR, JUPYTER_DATA_DIR,
JUPYTER_RUNTIME_DIR and IPYTHONDIR under `/tmp/pr11-review-round2/`.
It needs permission to create local sockets: the sandbox denied that on the
first attempt (`notebooks-sandbox.txt`), and the authorized retry passed
(`notebooks.txt`). This was an environment restriction, not a PR defect.

## Additional expected-behavior probes

Obtain `test_review_regressions.py` from this evidence directory. It imports
the reviewed implementation; it does not patch or replace any project code.
If the clone is elsewhere, update the script's `ROOT` path to the clone.
All fixture changes and mocked commands live in temporary directories.

```bash
/tmp/pr11-review-round2/env314/bin/python -m pytest -v --tb=short --color=no /tmp/pr11-review-round2/39c7d29/round-2/test_review_regressions.py -k 'not existing_paths'
/tmp/pr11-review-round2/env314/bin/python -m pytest -v -s --tb=short --color=no /tmp/pr11-review-round2/39c7d29/round-2/test_review_regressions.py -k existing_paths
```

Expected on the reviewed commit: the first invocation fails all 5 selected
assertions, one per review finding; the second passes all 5 selected cases.
The first two probes exercise the CLI in a temporary Git repository. The
workflow probes extract the exact shell script from the reviewed YAML and
run `bash -e -o pipefail` with a local `gh` stub. No workflow probe posts to
GitHub or supplies a real credential. Live bot posting remains unverified.

## GitHub Markdown confirmation

`union-report.md` is output of `render_report` with a union annotation and a
single Mention at `quickstart.md:2`. Submit it to GitHub's renderer:

```bash
gh api --method POST markdown -f mode=gfm -f context=WillyOwl/docs-guardian -F text=@/tmp/pr11-review-round2/39c7d29/round-2/union-report.md
```

The response is preserved in `github-table-render.txt`; it drops the Pages
cell. `union-report-rendered.png` displays the source and the actual returned
HTML. This endpoint only renders Markdown; it creates no comment or PR.

## Artifact and screenshot provenance

`capture.py` stores exact command arguments, full combined stdout/stderr,
exit status, duration, working directory, UTC timestamp and reviewed SHA.
Each `.txt` has a matching `.png` and `.html`. Screenshots were captured by
Chromium from a local HTML viewer containing HTML-escaped command output.
They are log-viewer captures, not screenshots of a live terminal or GitHub UI.
ANSI color codes are removed for display; original output remains intact.
The long initial notebook sandbox traceback is explicitly abbreviated in
its viewer; its text log is complete. No other output is abbreviated.

`render_screenshots.py` contains the full screenshot procedure and
`screenshots.json` records each image's dimensions and SHA-256 hash. Run the
script with a working Chrome executable path to reproduce the captures.
The `union-report-rendered` viewer embeds GitHub's returned HTML as-is.

Results are scoped to the reviewed SHA. Implementation files were not edited,
no fixes were pushed, and PR #11 was not merged.
