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
| `ci` | All six checks pass on 1c1ae38, and the drift job ran the new script |

`tools/check.sh` is the capture function. The posting tests run the real `.github/scripts/post-drift-report.sh` against a stub `gh`, and nothing is posted to GitHub. A live post, then a rewrite on a second push, is still unverified: this PR changes no tinyml API.
