# Verification steps — PR #12 round 2

Source: `eab5b3ca743838c270066d5c3f72f9a13582832a`; base: `d48615c3386b813d0fc6845a23e1588e3c57bf67`. Exact commands, UTC capture times and exit codes appear in each raw `.txt` log. Same-name `.png` files are fresh browser screenshots of those captured outputs, not synthetic terminal results. The two `root-relative-*.png` Page images come from the actual built mutation site.

## Setup

1. Create a detached checkout at the source commit under `$PR12_REVIEW_ROOT/source`; keep mutation copies outside it. The original run used `/tmp/pr12-review-round2`.
2. Install the locked Python dependencies with `uv sync --locked`; have Python 3.11 and 3.14 environments available. The capture used existing environments with `PYTHONPATH` selecting the pinned checkout and Guarded Project source.
3. Use markdownlint-cli2 **0.24.0**, Vale **3.26.0**, and lychee **0.24.2**. The cached release archives matched the workflow SHA-256 pins (`tool-versions.txt`). The harness accepts `PR12_REVIEW_ROOT`, `PR12_REVIEW_PYTHON`, `PR12_REVIEW_PY311`, `LYCHEE_BIN`, `VALE_BIN`, and `MARKDOWNLINT_BIN` overrides; set them to local executables. The optional archive-hash check's original cache path is recorded in the tool.
4. Set `NO_MKDOCS_2_WARNING=1` as CI does. Allow outbound network for the online link checks. The scripts redact credential-like environment values from captured output and do not print environment dumps or authorization headers.

## Baseline checks

The capture tool is `tools/run_checks.py`. Invoke each case as `python3 tools/run_checks.py <case>`:

| Case | Expected |
| --- | --- |
| `pytest-311` | 111 passed, harness exit 0 |
| `pytest-314` | 111 passed, harness exit 0 |
| `link-regressions` | 4 passed, harness exit 0 |
| `markdownlint` | no issues, exit 0 |
| `vale` | no errors, exit 0 |
| `strict-build` | site builds strictly, exit 0; run before `links` |
| `links` | online checks: 143 OK, 0 errors, exit 0 |
| `ruff` | lint and format pass, exit 0 |
| `ci` | pinned PR head and 10 successful checks, exit 0 |
| `integrity` | pinned SHA, no source diff or untracked files, diff whitespace check passes |

`strict-build` creates an untracked `source/.cache/`. Move that generated cache outside the source checkout before the final integrity check; the build site itself is gitignored. The initial cache observation and final clean result are both retained. Do not delete user files.

## Prior-fix verification

- `same-site-fixed`: append the original invalid same-site URL in a new scratch copy, show the mutation diff, build strictly, run the actual wrapper. Build exit 0, links exit 2 naming the missing target, harness exit 0.
- `notebook-anchor-fixed`: append the original invalid-anchor notebook cell in another scratch copy. Build exit 0, links exit 2 naming the missing fragment, harness exit 0.
- Each scratch-copy case deliberately refuses an existing destination; use a fresh review root or a new case directory when rerunning.

## New P2 feedback loop

```bash
python3 tools/reproduce_root_relative.py
```

Expected on the reviewed head: two underlying wrapper exits of **2**, `provide a root dir`, harness exit **1**. The sole link is `/docs-guardian/quickstart/`, and its destination exists. The loop expects the valid link to pass, so it will become exit 0 when corrected.

`root-relative-actual` captures the realistic source mutation and real MkDocs output: strict build exit 0, rendered href and target ID present, links exit 2. Its harness exit 0 means that it confirmed the reported defect, not that the source is fixed.

`root-relative-controls` runs the same lychee options and same HTML with and without one extra `--root-dir` argument. A temporary web root mounts the fixture under `docs-guardian/`, matching deployment. Adding the root context passes the valid link, and a missing destination still fails. No source fix is applied.

`boundary-probes` also retains relative, same-site and heading controls. Its exit 1 identifies only `valid-root-relative` as a failed contract.

The Spec reviewer's original logs and minimal HTML fixtures are preserved under `spec-probes/`; their source paths refer to the original review host. Parent-run captures provide independent reproductions of the same finding.

## Screenshots

`node tools/render_screenshots.cjs` uses Playwright Chromium. Override `PLAYWRIGHT_CORE_MODULE` and `CHROMIUM_BIN` if needed. It first serves the actual mutation build through request interception at its configured `site_url`, clicks the valid link, and checks that `h1#quickstart` is visible. External requests are aborted. This demonstrates local build behavior under deployment URL semantics and does not contact the live site.

It then screenshots every saved `.txt` log, retaining its full output. `screenshots.json` maps logs to images. The evidence index links logs, screenshots and reports; `manifest.json` records artifact hashes.
