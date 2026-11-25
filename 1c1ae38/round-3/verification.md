# Reproducing review round 3

Reviewed source: `1c1ae382b858fb9c3aa9d8303a590df02773a34c`.
Comparison base: `6af3ec1c790f170e064659a1f23ae2e1f6008c04`.
Evidence location: `pr11-review-evidence`, `1c1ae38/round-3/`.

The source checkout is a detached worktree at `/tmp/pr11-review-round3/source`.
The evidence directory is separate from it, so review-only probes do not
change the PR's source or test suite. Each raw log records the reviewed SHA,
UTC timestamp, working directory, environment, exact commands, exit statuses,
and duration. See `environment.txt` for interpreter and dependency versions.

## Commands

From the source checkout, select tooling and Guarded Project code explicitly:

```bash
export PYTHONPATH="$PWD/src:$PWD/tinyml/src"
python -m pytest -p no:cacheprovider --color=no
python -m ruff check .
python -m ruff format --check .
python -c 'from docs_guardian.cli import main; raise SystemExit(main())' snippets tinyml/docs
python -c 'from docs_guardian.cli import main; raise SystemExit(main())' drift --base origin/main --source tinyml/src --docs tinyml/docs
python -m pytest --nbmake tinyml/docs/notebooks -p no:cacheprovider --color=no
python -m mkdocs build --strict -f tinyml/mkdocs.yml -d /tmp/pr11-review-round3/site
```

Run the full suite with Python 3.11 and 3.14 separately. nbmake and MkDocs
require the docs dependency group. The exact environments used here are in
`capture.py`; adapt its paths for another machine. It reuses existing
environments and does not install dependencies. For a fresh installation use
the repository's documented uv setup.

Review probes and the isolated CLI report:

```bash
python -m pytest /path/to/evidence/test_review_round3.py -vv --tb=short -p no:cacheprovider --color=no
python /path/to/evidence/report_demo.py
gh api --method POST markdown -f mode=gfm -F text=@/path/to/evidence/report-demo.md
gh pr checks 11 --repo WillyOwl/docs-guardian
gh pr view 11 --repo WillyOwl/docs-guardian --json headRefOid,state,isDraft
```

Set `ROOT` in the probe file to the reviewed source checkout. The demo creates
and removes its own temporary Git fixture; its `main` is that fixture's branch,
not this repository's main. It writes the actual CLI report to `report-demo.md`.
The full GitHub-rendered response is saved separately as
`report-demo-github.html` and remains in `github-render.txt` with the command.

## Output and screenshot index

Each row links unedited command output and its new screenshot.

| Check | Output | Screenshot |
| --- | --- | --- |
| Full suite, Python 3.11.15 | [log](pytest-3.11.txt) | [image](pytest-3.11.png) |
| Full suite, Python 3.14.6 | [log](pytest-3.14.txt) | [image](pytest-3.14.png) |
| 17 independent probes | [log](review-probes.txt) | [image](review-probes.png) |
| Ruff lint and format | [log](ruff.txt) | [image](ruff.png) |
| Snippet runner | [log](snippets.txt) | [image](snippets.png) |
| Notebook, sandbox socket failure | [log](notebooks-sandbox.txt) | [image](notebooks-sandbox.png) |
| Notebook, authorized successful rerun | [log](notebooks.txt) | [image](notebooks.png) |
| Strict docs build | [log](build-docs.txt) | [image](build-docs.png) |
| Current PR Drift Report | [log](drift-current.txt) | [image](drift-current.png) |
| Isolated CLI report fixture | [log](report-demo.txt) | [image](report-demo.png) |
| Real GitHub Markdown response | [log](github-render.txt) | [image](github-render.png) |
| GitHub-rendered report | [Markdown input](report-demo.md) and [response HTML](report-demo-github.html) | [input and output image](report-demo-rendered.png) |
| GitHub CI | [log](ci.txt) | [image](ci.png) |
| Environment and checkout | [log](environment.txt) | [image](environment.png) |

## Screenshot provenance

`render_screenshots.py` launches the installed Chromium headless shell and
captures local HTML pages made from the saved logs. Log screenshots contain
the entire output; only ANSI color escapes are removed for display. These
are screenshots of a log viewer, not screenshots of a live terminal or the
GitHub PR interface. The original logs are retained without editing.

`report-demo-rendered.png` displays the actual HTML response from GitHub's
Markdown API beneath the CLI's input. It is not evidence of a bot posting a
comment. The renderer checks that the returned table retains two body rows
and three cells per row, including the union signature, backtick default,
special Page filename, and notebook cell location.

`screenshots.json` records each screenshot's source, dimensions, reviewed
commit, image SHA-256, and source-log SHA-256. The corresponding HTML files
are stored alongside every image. Rerun `render_screenshots.py` after adapting
its browser path if necessary.
