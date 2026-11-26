# Evidence at eab5b3c: fixes for review round 1

Every `.txt` file is a command's full output, with ANSI colour codes removed. Its first line is the command, run in a detached worktree:
- `wt`: `eab5b3c`, the fixes;
- `wt-old`: `e7db35c`, the commit round 1 reviewed.

Each `.png` is its `.txt` rendered by `tools/render.cjs` in headless Chromium. Scratchpad paths are shortened to `<scratchpad>`. `fixtures/` holds the reviewer's two fixtures, copied unchanged from `e7db35c/round-1/fixtures/`.

| File | What it shows |
| --- | --- |
| `spec1-same-site-before-fix` / `-fixed` | The reviewer's `same-site-url.patch` on the real tinyml build. At e7db35c the dead same-site link is "Excluded" and the run exits 0; at eab5b3c it is remapped to the local build: `File not found`, exit 2 |
| `spec2-notebook-anchor-before-fix` / `-fixed` | The reviewer's minimal notebook, with a link to a missing `#heading`. At e7db35c it is "OK", exit 0; at eab5b3c: `Cannot find fragment`, exit 2. The strict build passes both times, as the review said |
| `check-links-tests` | `tests/test_check_links.py`: 4 passed, with lychee 0.24.2 |
| `links` | The real tinyml build with the fixed rules: 0 errors (the live-site links are now checked, 143 OK) |
| `markdownlint`, `vale`, `strict-build` | Unchanged by these fixes; fresh runs at eab5b3c |
| `pytest-3.14`, `pytest-3.11`, `ruff` | Full suite (111 passed) and lint |
| `ci` | All ten PR checks pass on eab5b3c; the `links` job ran the 4 new tests |

## Independent review round 2

[Review, fresh test output, screenshots, and verification steps](round-2/README.md). The prior two findings are verified fixed; one new P2 root-relative link false positive remains open on this source commit.
