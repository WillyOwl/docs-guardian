# Self-review bug hunt before the live demo: PR #11 at 1c1ae38

**Asked:** before opening a short-lived demo PR that changes tinyml's API, check whether PR #11 has any code bugs. Round 3 (on the same commit) had reported no new correctness findings.

**Method (diagnosing-bugs):** with no reported symptom, the feedback loops were built to go red on unseen bugs, and each was shown to be red-capable before it was trusted.

1. **Property loops** (`tools/fuzz.py`, 3 seeds × 3000 rounds each):
   - Every inline code span is reported on the line where it starts, in random pages with lists, quotes, headings, links and multi-line spans.
   - `_code` round-trips any text through a GFM table cell.
   - No JSON value read as a notebook raises.

   On the commit round 2 reviewed (39c7d29), the same loops go red on all three (109 / 452 / 121 counterexamples in 300 rounds), so they would have caught F2, F3 and F5.
2. **CLI scenario loop** (`tools/scenarios.py`): 19 adversarial runs of `docs-guardian drift` in temporary git repos, among them:
   - `--source .`, a run from a subdirectory, absolute paths, trailing slashes;
   - a SHA as the base, a detached HEAD;
   - a package or source folder that's new since the base, a deleted module;
   - CRLF and BOM Pages, a symlinked module, a git-ignored build copy;
   - an unwritable `--output`, a latin-1 coding cookie, docs inside the source folder, no git repo;
   - a Page holding only a Skipped Snippet.

   Each run asserts its exit code, a line of the report, and no traceback.
3. **Truncation sweep** (`tools/sweep.sh`): a report over the 60,000-byte limit, shifted by 0–45 bytes so the cut lands at every offset of a table row. It runs the real posting script against a stub `gh`, and checks that the step succeeds and that the body it sends is valid UTF-8.

The early oracle failures were in the generator, not the code, and were fixed one at a time:
- stray backticks that legally pair with later spans;
- a line count that ignored newlines inside multi-line spans;
- a heading continued onto a second line;
- `<b>` at the start of a line, which opens an HTML block;
- cell strings with spaces at both ends, which CommonMark strips by design. No signature, name or Page path has them.

## Findings

| # | Bug | Loop that went red | Confirmed cause | Fixed in |
| --- | --- | --- | --- | --- |
| H1 | A module with a PEP 263 coding cookie (`# -*- coding: latin-1 -*-`), valid Python, is listed as unreadable and its new API is missed | CLI scenario `latin1_coding_cookie` | Both sides decoded sources as UTF-8 with `errors="replace"` before `ast.parse`, discarding the cookie. Probe: `ast.parse` on the raw bytes returns `['café', 'plain']` | `1baca4a` |
| H2 | `--output` into a missing folder ends in a traceback and exit 1, not the misconfiguration exit 2 | CLI scenario `output_into_missing_folder` | `cli._run_drift` wrote the file with no `OSError` handling | `1baca4a` |
| H3 | Files git ignores under `--source` (a build copy) count as API locally, but never in CI's clean checkout | CLI scenario `ignored_build_copy` (sharpened: the first version reused `fit`'s signature and proved nothing) | `_source_in_checkout` walked the disk with `rglob`, which ignores `.gitignore`. Probe: `git ls-files --cached --others --exclude-standard` keeps tracked and new files and drops the ignored one | `1baca4a` |
| H4 | A report over 60,000 bytes can be cut inside a 3-byte `→`; GitHub then shows `��` | Truncation sweep: 2 of 46 alignments | `head -c` counts bytes. GitHub's render endpoint accepts the body, so the effect is cosmetic. A first fix piped through `iconv -c`, but iconv exits 1 when it drops a character, which aborted the step under `-e -o pipefail`. Caught by the regression test before commit | `5de9401` |

**Falsified:** a NUL byte in a module raising `ValueError` (uncaught) on Python 3.11. Both 3.11 and 3.14 raise `SyntaxError`, which is handled.

**Clean on every loop:** Mention lines, table cells and notebook shapes (the 9,000-round fuzz on each), and the other 16 CLI scenarios.

**Not covered by any loop:** a live bot comment (first POST, then PATCH on a second push). That's the demo PR's job.
