# Evidence at 7b5a100: fixes for review round 5

Every `.txt` file is a command's full output, with ANSI colour codes removed. Its first line is the command, run in a detached worktree of `7b5a100` (`wt-new`), or of `77120b7` (`wt-prev`), the commit round 5 reviewed. Each `.png` is its `.txt` rendered by `tools/render.cjs` in headless Chromium. Scratchpad paths are shortened to `<scratchpad>`.

| File | What it shows |
| --- | --- |
| `pytest-3.14`, `pytest-3.11` | Full suite at 7b5a100: 107 passed on Python 3.14.10 and 3.11.15 |
| `round5-tests-before-fix` / `round5-tests-fixed` | The 4 new regression tests copied onto 77120b7: 4 red; at 7b5a100: 4 pass |
| `reviewer-probes` | The reviewer's `77120b7/round-5/test_review_round5.py`, unchanged (copy in `tools/`): 7 passed |
| `hunt-loops` | Round 4's CLI scenarios (19/19) and property loops (3000 rounds) re-run: no regression |
| `ruff`, `snippets`, `drift-this-pr` | Lint and format, the snippet runner, and this PR's own Drift Report |
| `drift-demo` | The build guide's demo on a scratch edit of tinyml |
| `drift-misconfigured` | A mistyped `--docs` and an unwritable `--output`: both exit 2 |
| `ci` | All six checks pass on 7b5a100 |
