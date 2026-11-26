# Reproduction and interpretation

## Environment and provenance

The baseline was a clean detached worktree of PR #12 at `e7db35cdf9cd8c70e63dc592d821f9243875dc76`. The root project's already installed Python 3.14.6 environment provided dependencies; `PYTHONPATH` pointed to the review worktree's `src/` and `tinyml/src/`, so tests imported the reviewed sources. Tools used the PR's versions: Markdownlint 0.24.0, Vale 3.26.0, lychee 0.24.2. `tool-versions.txt` records exact versions and binary hashes. No credential values are needed for local reproductions; any sensitive environment values are removed from captured output before screenshots are generated.

MkDocs was invoked as `python -m mkdocs build --strict -f tinyml/mkdocs.yml` from the review root. This loads the same configuration, plugins and dependencies as `uv run mkdocs build --strict` from `tinyml/`. Its generated root `.cache/` was moved into a separate temporary output folder before the clean-worktree check. Normal CI's `tinyml/.cache/` is git-ignored.

## Commands run in this review

Every log includes exact argv, working directory, complete combined output, and exit codes. The controlling commands were:

```bash
python3 /tmp/pr12-review/run_checks.py tool-versions
python3 /tmp/pr12-review/run_checks.py markdownlint
python3 /tmp/pr12-review/run_checks.py vale
python3 /tmp/pr12-review/run_checks.py strict-build
python3 /tmp/pr12-review/run_checks.py links
python3 /tmp/pr12-review/run_checks.py pytest
python3 /tmp/pr12-review/run_checks.py ruff
python3 /tmp/pr12-review/run_checks.py ci
python3 /tmp/pr12-review/run_checks.py notebook-anchor
python3 /tmp/pr12-review/run_checks.py notebook-anchor-online
python3 /tmp/pr12-review/run_checks.py notebook-anchor-minimal
python3 /tmp/pr12-review/run_checks.py anchor-controls
python3 /tmp/pr12-review/run_checks.py same-site-url
python3 /tmp/pr12-review/run_checks.py same-site-url-online
python3 /tmp/pr12-review/run_checks.py same-site-controls
python3 /tmp/pr12-review/run_checks.py source-integrity
node /tmp/pr12-review/render_screenshots.cjs
```

The `*-anchor*` and `same-site-url*` reproduction commands intentionally return **1** when both Gates incorrectly accept the planted error. This is the red feedback loop. A `diff` command returning 1 in those logs proves the mutation differs from pristine source; it is not itself a test failure. The `*-controls` scripts return 0 only after verifying the diagnostic flag makes the bad destination fail and the positive control passes.

## Repeat independently

Install dependencies and the pinned tools as documented in README and `.github/workflows/docs-lint.yml`. Use a fresh temporary review directory, because the harness refuses to overwrite existing mutation directories.

```bash
git worktree add --detach /tmp/pr12-recheck/source e7db35cdf9cd8c70e63dc592d821f9243875dc76
uv sync --locked --directory /tmp/pr12-recheck/source
export PR12_REVIEW_ROOT=/tmp/pr12-recheck
export PR12_REVIEW_PYTHON=/tmp/pr12-recheck/source/.venv/bin/python
export VALE_BIN=/absolute/path/to/vale
export LYCHEE_BIN=/absolute/path/to/lychee
export MARKDOWNLINT_BIN=/absolute/path/to/markdownlint-cli2

# Run these from any directory after downloading tools/run_checks.py.
python3 tools/run_checks.py notebook-anchor
python3 tools/run_checks.py anchor-controls
python3 tools/run_checks.py same-site-url
python3 tools/run_checks.py same-site-controls
```

Run `notebook-anchor` before `anchor-controls` and `same-site-url` before `same-site-controls`, because the controls reuse their generated mutation sites. Add the `*-online` cases to verify the original network-enabled CLI behavior. The offline cases make only local-destination assertions and finish in seconds, independently of remote availability. Online captures in this evidence establish that both holes remain under the original workflow's network-enabled invocation.

## Minimal changes

- Notebook: append a Markdown cell with `[Review missing heading](#pr12-review-missing-heading)`. The minimized notebook consists only of that cell and valid notebook metadata; see `fixtures/notebook-anchor-minimal.ipynb`.
- Same-site URL: append `[Review missing page](https://willyowl.github.io/docs-guardian/pr12-review-missing-page/)` to `tinyml/docs/index.md`. See `fixtures/same-site-url.patch`.
- The rendered fixtures contain those links and have no matching target ID/file. Browser DOM assertions and control logs verify that the fixture reaches the real output.

The `--include-fragments=anchor-only` and `--remap` controls are isolated experiments. Neither change was added to the PR's source configuration during this review.
