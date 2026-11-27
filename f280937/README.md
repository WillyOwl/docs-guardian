# PR #19 evidence: commit `f280937`

Every log below was captured against `f280937` (the PR's head), and each `.png` is a headless-Chrome rendering of the `.txt` next to it (`render.sh`), except `demo-pr23-page.png`, a headless-Chrome capture of the public page of Demo PR #23.

| Evidence | Result | Files |
| --- | --- | --- |
| e2e suite, `--e2e-base test/e2e-demo-prs` | 4 passed; Demo PRs #23, #24, #25 opened, asserted, closed, branches deleted | `e2e.txt`, `e2e.png` |
| Drift Report on Demo PR #23 after both pushes | one comment, created 02:35:17, rewritten in place 02:36:13: no Drift | `drift-report-pr23.txt`, `drift-report-pr23.png` |
| Demo PR #23 as GitHub shows it | ✗ on the rename commit, ✓ on the docs fix, the bot's comment "edited", closed, branch deleted | `demo-pr23-page.png` |
| `uv run pytest` | 108 passed, 4 skipped (lychee not installed locally; CI's `links` job runs them), 4 deselected (the e2e suite) | `pytest.txt`, `pytest.png` |
| ruff check + format | clean | `ruff.txt`, `ruff.png` |
| PR #19's checks on `f280937` | all 10 succeed | `ci.txt`, `ci.png` |

## Verification steps

1. `uv run pytest`: the e2e tests are deselected (`4 deselected`), so plain pytest and CI never open PRs.
2. `git push` the branch, then `uv run pytest -m e2e -v -rA --e2e-base test/e2e-demo-prs`.
3. Afterwards: `gh pr list --label e2e --state open` is empty and `git ls-remote --heads origin 'demo/*'` prints nothing.

## Earlier attempt

`../47661e0/e2e-interrupted.txt`: the first run on this branch, at `47661e0`. GitHub left the `ruff` job on Demo PR #22 at status `in_progress` after it had concluded `success`, and refused to cancel or re-run it, so the suite waited until I interrupted it. The interrupt (a `pkill` that also hit the `uv` wrapper) skipped cleanup, so #20, #21 and #22 were closed and their branches deleted by hand. `f280937` makes the suite wait for each check's conclusion instead of its status.
