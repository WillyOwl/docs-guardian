# PR #11 round-9 verification

Reviewed head: `7b5a100481ec7a078551d307325c3f422f48793b`.
All commands ran from a fresh detached worktree at that commit.
Existing disposable virtual environments were reused without dependency changes.
`PYTHONPATH` explicitly selects this checkout's `src` and `tinyml/src`; module
paths and dependency versions are recorded in `environment.txt`.

## Results and screenshots

| Check | Result | Full output | Fresh screenshot |
| --- | --- | --- | --- |
| Environment and clean checkout | Verified | [log](environment.txt) | [image](environment.png) |
| Python 3.11 suite | 107 passed | [log](pytest-3.11.txt) | [image](pytest-3.11.png) |
| Python 3.14 suite | 107 passed | [log](pytest-3.14.txt) | [image](pytest-3.14.png) |
| Independent review probes | 7 failed, 6 controls passed | [log](review-probes.txt) | [image](review-probes.png) |
| F1 module aliases | Removal found, Drift Page missed | [log](f1-reproduction.txt) | [image](f1-reproduction.png) |
| F2 admonition code | Rendered code missed | [log](f2-reproduction.txt) | [image](f2-reproduction.png) |
| F3 notebook Markdown | Inline code missed | [log](f3-reproduction.txt) | [image](f3-reproduction.png) |
| F4 last module removed | Exit 2, no report | [log](f4-reproduction.txt) | [image](f4-reproduction.png) |
| Combined CLI reproductions | Four discrepancies demonstrated | [log](finding-reproductions.txt) | [image](finding-reproductions.png) |
| Ruff lint and format | Pass, 26 files formatted | [log](ruff.txt) | [image](ruff.png) |
| Snippets | 4 Pages pass | [log](snippets.txt) | [image](snippets.png) |
| Notebook | 1 passed | [log](notebooks.txt) | [image](notebooks.png) |
| Notebook initial sandbox attempt | Kernel socket blocked by sandbox | [log](notebooks-sandbox.txt) | [image](notebooks-sandbox.png) |
| MkDocs strict build | Pass | [log](build-docs.txt) | [image](build-docs.png) |
| Drift on unmodified PR checkout | No API Changes, exit 0 | [log](drift-current.txt) | [image](drift-current.png) |
| GitHub CI and PR head | Six checks pass; reviewed head confirmed | [log](ci.txt) | [image](ci.png) |
| Final source and remote provenance | Head and clean source confirmed | [log](head-provenance.txt) | [image](head-provenance.png) |

The [probe source](test_review_round9.py) creates disposable git repositories:
`main` defines `fit_linear(X, y)`, then the feature checkout removes it.
The independent expected result is an API removal and Drift on the Page using it.
F4 deletes the last module but preserves the configured source directory.
Controls distinguish real API use from prose and unrelated object attributes,
check direct package access and notebook code cells, and verify site rendering.

## Reproduce

Use a checkout of the reviewed SHA and install its workspace and docs dependencies
with `uv sync --locked`. For the independent probes and CLI reproductions:

```bash
uv run pytest /absolute/path/to/test_review_round9.py -vv --tb=short -p no:cacheprovider
uv run python /absolute/path/to/reproduce_findings.py
```

The probes are expected to return 1 at this head: seven assertions expose four
bugs. The reproduction script returns 0 after logging the four discrepancies;
each embedded CLI exit code and expected result is shown explicitly.

[capture.py](capture.py) retains the exact commands, working directory, captured
output, timestamps, and exit statuses used in this run. Its hardcoded temporary
paths refer to this review environment; they are not project configuration.
[render_screenshots.py](render_screenshots.py) opens the saved log HTML in Chromium
and captures the full viewport. The [manifest](screenshots.json) records the
reviewed commit, viewport, image hashes, and source-log hashes. The separate
[rendered examples](site-rendered-examples.html) show Page syntax using the
site's actual Python-Markdown extensions.

Notebook tests need local Jupyter kernel sockets. Their initial sandbox failure
was preserved before the successful authorized retry. The MkDocs build's only
untracked cache was moved out of the source worktree; the reviewed source stayed
unchanged. No live report comment was posted or rewritten by the workflow during
these checks. README updated by the PR; README unaffected by this review.
