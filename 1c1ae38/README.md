# Evidence at 1c1ae38: fixes for review round 2

Every `.txt` file is a command's full output, with ANSI colour codes removed. The first line of each is the command, run in a detached worktree of `1c1ae38` (`wt-fix`), or of the reviewed `39c7d29` (`wt-old`). Each `.png` is that `.txt` file rendered by `tools/render.cjs`, a headless-Chromium log viewer; they are not terminal screenshots. Long scratchpad paths are shortened to `<scratchpad>`.

| File | What it shows |
| --- | --- |
| `pytest-3.14`, `pytest-3.11` | The full suite at 1c1ae38: 99 passed on Python 3.14.10 and 3.11.15 |
| `round2-tests-before-fix` | The new tests copied onto the reviewed 39c7d29, with its inline posting script extracted verbatim: 9 red, one or more per finding, plus 2 self-found |
| `round2-tests-fixed` | The same 17 tests at 1c1ae38: all pass |
| `reviewer-probes` | The reviewer's own `39c7d29/round-2/test_review_regressions.py`, with the two changes shown in `tools/probe-adaptation.diff` (ApiChange now takes tuples; the posting script is its own file): 10 passed |
| `github-render` | `tools/make_report.py` renders a report with a union, a backtick and a `\|` in a Page name; GitHub's `POST /markdown` keeps all three cells |
| `ruff`, `snippets`, `drift-this-pr` | Lint and format, the snippet runner on tinyml's Pages, and this PR's own Drift Report |
| `drift-demo` | The build guide's demo on a scratch edit of tinyml (`fit_linear` renamed to `fit`, `metric` added to `evaluate`): both changes with their exact Pages, lines and notebook cells, and `fit` not yet documented |
| `drift-misconfigured` | A mistyped `--docs` exits 2 |
| `ci` | All six checks pass on 1c1ae38, and the drift job ran the new script |

`tools/check.sh` is the capture function. The posting tests run the real `.github/scripts/post-drift-report.sh` against a stub `gh`, and nothing is posted to GitHub. A live post, then a rewrite on a second push, is still unverified: this PR changes no tinyml API.

## Independent review round 3

The latest independent review, fresh test output and 14 screenshots are in
[`round-3/`](round-3/): [review](round-3/review.md),
[verification and complete index](round-3/verification.md).
