# Verification steps — PR #12, round 3

Source: `e1f15ea6789dc0d566c3c8d997a864419529fd83`. Base: `d48615c3386b813d0fc6845a23e1588e3c57bf67`. All captures were made against that exact head on 2026-11-26 UTC. Evidence belongs under `e1f15ea/round-3/` on `pr12-review-evidence`.

The source was checked out in an isolated detached worktree at `/tmp/pr12-review-round3/source`. Existing Python environments and cached tools were reused, with `PYTHONPATH` pointing at this checkout's `src/` and `tinyml/src/`. No dependency manifest changed in this PR. Tool versions and binary-archive SHA-256 pins were verified in `tool-versions.txt`; this was not a fresh dependency installation. Both full suites set `LYCHEE` to the installed pinned binary, so the new link tests run rather than skip.

## Captured checks

The exact executable paths, working directories, timestamps, output and exit codes are in every `.txt` log. `tools/run_checks.py` records and redacts output. Its constants identify the existing tools in this environment; adjust these paths when reproducing elsewhere.

```bash
git worktree add --detach /tmp/pr12-review-round3/source e1f15ea6789dc0d566c3c8d997a864419529fd83
python /tmp/pr12-review-round3/run_checks.py tool-versions
python /tmp/pr12-review-round3/run_checks.py pytest-314
python /tmp/pr12-review-round3/run_checks.py pytest-311
python /tmp/pr12-review-round3/run_checks.py link-regressions
python /tmp/pr12-review-round3/run_checks.py markdownlint
python /tmp/pr12-review-round3/run_checks.py vale
python /tmp/pr12-review-round3/run_checks.py ruff
python /tmp/pr12-review-round3/run_checks.py strict-build
python /tmp/pr12-review-round3/run_checks.py links
python /tmp/pr12-review-round3/run_checks.py snippets
python /tmp/pr12-review-round3/run_checks.py notebooks
python /tmp/pr12-review-round3/run_checks.py boundary-probes
python /tmp/pr12-review-round3/run_checks.py lint-controls
python /tmp/pr12-review-round3/run_checks.py strict-controls
python /tmp/pr12-review-round3/run_checks.py original-repros
python /tmp/pr12-review-round3/run_checks.py 404-coverage
python /tmp/pr12-review-round3/run_checks.py ci
python /tmp/pr12-review-round3/run_checks.py integrity
```

Build before running `links` or `404-coverage`. Run each mutation case only once in a fresh scratch root; the script refuses to overwrite existing mutation copies. All mutations are scratch copies; no change is applied to the pinned source.

## Confirmed failing contract

```bash
python /tmp/pr12-review-round3/run_checks.py escape-minimal
# EXPECTED harness exit 1: real Gate incorrectly exits 0 for an unpublished target.
python /tmp/pr12-review-round3/run_checks.py escape-real
# EXPECTED harness exit 1: strict build + real online Gate both incorrectly exit 0.
python /tmp/pr12-review-round3/run_checks.py escape-controls
# EXPECTED exit 0: repeated bug and one-variable diagnosis controls match predictions.
python /tmp/pr12-review-round3/run_checks.py live-destination
# EXPECTED exit 0 at capture time: https://willyowl.github.io/README.md returns HTTP 404.
```

The first command is a deterministic, network-free reproduction taking milliseconds. The real notebook build and `live-destination` additionally require network access; public HTTP status is a point-in-time observation, not the deterministic feedback loop.

`fixtures/escape-minimal/` stores the entire minimal fixture. `fixtures/escape-notebook.ipynb` stores the mutated real notebook. `spec-probe.md` contains independently captured commands and output, including an offline-only real-notebook probe; the primary `escape-real.txt` probe used the actual script with online checks enabled.

## Screenshots

```bash
node /tmp/pr12-review-round3/render_screenshots.cjs
node /tmp/pr12-review-round3/render_screenshots.cjs --logs-only
```

`tools/render_screenshots.cjs` uses Chromium through Playwright. Every command-output screenshot is a browser capture of the accompanying freshly captured raw log; the HTML rendering is included. `screenshots.json` maps every log to its screenshot. `escape-notebook-rendered.png` is the actual generated notebook Page with the fixture link visually highlighted; `escape-browser-destination.png` shows the local publication replay after following it. Browser routing serves only the actual built files under `/docs-guardian/` and deliberately responds 404 outside that path. These are not live-deployment screenshots. `browser-dom.txt` captures the assertions and URL, and `live-destination.txt` separately captures the real HTTP 404.

## Preserved attempts and limitations

- `notebooks-sandbox-attempt.txt`: Jupyter could not create a local kernel socket in the restricted sandbox (`Operation not permitted`). Rerunning with local sockets allowed passed: `notebooks.txt`.
- `404-coverage-sandbox-attempt.txt`: the intended missing-link diagnostic appeared along with unrelated sandbox HTTP errors. The fresh online `404-coverage.txt` isolates exactly the one introduced broken link, with all 157 baseline checks OK.
- `escape-controls-harness-attempt.txt`: a diagnostic assertion incorrectly expected verbose lychee to include the accepted filename; the output only printed its summary. The corrected harness asserts `1 OK`; `escape-controls.txt` contains the completed controls. This was a harness correction and no source code changed.

Every preserved attempt also has a screenshot. No before/after source fix is claimed in this review. The failure remains open; no merge was performed.
