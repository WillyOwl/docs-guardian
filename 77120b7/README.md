# Evidence at 77120b7: the self-review bug hunt's fixes

Every `.txt` file is a command's full output, with ANSI colour codes removed. Its first line is the command, run in a detached worktree:
- `wt-new`: `77120b7`, the fixes;
- `wt-prev`: `1c1ae38`, before them, the commit round 3 reviewed;
- `wt-r1`: `39c7d29`, the commit round 2 reviewed.

Each `.png` is its `.txt` rendered by `tools/render.cjs` in headless Chromium. Scratchpad paths are shortened to `<scratchpad>`. `hunt-report.md` is the raw report of this review round.

| File | What it shows |
| --- | --- |
| `pytest-3.14`, `pytest-3.11` | Full suite at 77120b7: 103 passed on Python 3.14.10 and 3.11.15 |
| `hunt-tests-before-fix` / `hunt-tests-fixed` | The 4 new regression tests copied onto 1c1ae38: 4 red; at 77120b7: 4 pass |
| `cli-scenarios-before-fix` / `-fixed` | `tools/scenarios.py`: 3 red on 1c1ae38 (H1, H2, H3); 19 of 19 pass at 77120b7 |
| `truncation-sweep-before-fix` / `-fixed` | `tools/sweep.sh` on the real posting script: 2 of 46 alignments send invalid UTF-8 on 1c1ae38 (H4); 0 of 46 at 77120b7 |
| `fuzz-fixed` | `tools/fuzz.py`, 3 seeds × 3000 rounds at 77120b7: no counterexample |
| `fuzz-red-capable-on-39c7d29` | The same loops on 39c7d29 find 109 / 452 / 121 counterexamples (F5, F2, F3), so they can go red |
| `ruff`, `snippets`, `drift-this-pr` | Lint and format, the snippet runner, and this PR's own Drift Report |
| `drift-demo` | The build guide's demo on a scratch edit of tinyml: both changes with exact Pages and cells, `fit` not yet documented |
| `drift-misconfigured` | A mistyped `--docs`, and an unwritable `--output`: both exit 2 with one line |
| `ci` | All six checks pass on 77120b7; the drift job runs the posting script |
