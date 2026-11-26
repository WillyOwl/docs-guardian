# Evidence at e1f15ea: fixes for review round 2

Commits: `5be3646` (root-relative links resolve against the build) and `e1f15ea` (`404.html` no longer excluded).

Every `.txt` file is a command's full output, with ANSI colour codes removed. Its first line is the command, run in a detached worktree:
- `wt`: `e1f15ea`, clean, never modified;
- `mut`: `e1f15ea`, where the fixtures are applied;
- `mut-old`: `eab5b3c`, the commit round 2 reviewed, where the fixtures are applied.

`tools/capture.sh` produced every log except `ci.txt`, using `tools/check.sh`. Each `.png` is its `.txt` rendered by `tools/render.cjs` in headless Chromium. Scratchpad paths are shortened to `<scratchpad>`. `fixtures/` holds the reviewer's round 2 fixtures, copied unchanged from `eab5b3c/round-2/fixtures/`; `root-relative-actual.patch.git` is the same patch with `a/` and `b/` paths so `git apply` takes it.

| File | What it shows |
| --- | --- |
| `spec1-root-relative-before-fix` / `-fixed` | The reviewer's valid `/docs-guardian/quickstart/#quickstart` link on the real home Page. The strict build passes both times. At eab5b3c the link check fails with `Cannot resolve root-relative link ... provide a root dir`, exit 2; at e1f15ea it passes, 158 OK, exit 0 |
| `spec1-root-relative-missing` / `-unprefixed` | The same link pointed at `/docs-guardian/missing-page/`, then at `/quickstart/` (no deployment prefix, so broken on GitHub Pages). Both fail at e1f15ea: `File not found`, exit 2 |
| `red-test` | The new test, `test_a_root_relative_link_resolves_as_on_the_deployed_site`, run against eab5b3c's script: fails with the reported error |
| `check-links-tests` | `tests/test_check_links.py` at e1f15ea: 5 passed, with lychee 0.24.2 |
| `404-before-fix` | Why `404.html` was excluded: at eab5b3c, with only the exclusion removed, each of its `/docs-guardian/` links fails with `provide a root dir` |
| `links` | The real tinyml build at e1f15ea, `404.html` included: 157 OK, 0 errors (143 OK at eab5b3c) |
| `strict-build`, `markdownlint`, `vale` | Fresh runs at e1f15ea |
| `pytest-3.14`, `pytest-3.11`, `ruff` | Full suite (112 passed on each) and lint |
| `ci` | All ten PR checks pass on e1f15ea; the `links` job ran the 5 link tests and found 157 OK, 0 errors |
