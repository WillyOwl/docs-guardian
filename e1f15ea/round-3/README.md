# PR #12 review evidence — e1f15ea, round 3

Reviewed source: `e1f15ea6789dc0d566c3c8d997a864419529fd83`. Base: `d48615c3386b813d0fc6845a23e1588e3c57bf67`.
Captured 2026-11-26 UTC against the latest PR head, with no source changes.

**Result: Standards 0 findings; Spec 1 confirmed P2 finding.** Relative links can escape the published build and incorrectly pass by finding an unpublished checkout file. The actual public destination of the notebook reproduction returned HTTP 404. The defect remains open.

[Full diagnosis and per-point verdicts](review.md) · [Standards report](standards-review.md) · [Spec report](spec-review.md) · [Original specification](spec-source.md) · [Diff](diff.patch) · [Verification steps and limitations](verification.md) · [Capture script](tools/run_checks.py) · [Screenshot renderer](tools/render_screenshots.cjs).

## Checks and fresh screenshots

Screenshots of command output are browser captures of the matching raw logs, not screenshots of an interactive terminal. Each includes the source commit, capture time, command, actual output and verdict.

| Check | Result | Raw output | Fresh screenshot |
| --- | --- | --- | --- |
| pytest · Python 3.14 | 112 passed | [log](pytest-314.txt) | [screenshot](pytest-314.png) |
| pytest · Python 3.11 | 112 passed | [log](pytest-311.txt) | [screenshot](pytest-311.png) |
| Actual-script link tests | 5 passed; none skipped | [log](link-regressions.txt) | [screenshot](link-regressions.png) |
| Markdownlint 0.24.0 | 0 issues | [log](markdownlint.txt) | [screenshot](markdownlint.png) |
| Vale 3.26.0 | 0 errors / warnings / suggestions | [log](vale.txt) | [screenshot](vale.png) |
| Strict MkDocs build | passed | [log](strict-build.txt) | [screenshot](strict-build.png) |
| Real site / online lychee 0.24.2 | 157 OK; 0 errors, 142 unsupported non-URL tokens | [log](links.txt) | [screenshot](links.png) |
| Ruff lint + format | passed | [log](ruff.txt) | [screenshot](ruff.png) |
| Snippet runner | 4 Pages passed | [log](snippets.txt) | [screenshot](snippets.png) |
| Notebook execution | 1 passed | [log](notebooks.txt) | [screenshot](notebooks.png) |
| Valid/broken URL and anchor contracts | 12 cases passed | [log](boundary-probes.txt) | [screenshot](boundary-probes.png) |
| Previous-round failures on real builds | valid root-relative accepted; missing same-site Page and notebook heading rejected | [log](original-repros.txt) | [screenshot](original-repros.png) |
| Built 404.html mutation | one added broken link rejected; 157 OK / 1 intended error | [log](404-coverage.txt) | [screenshot](404-coverage.png) |
| Markdownlint / Vale negative controls | both mutations rejected | [log](lint-controls.txt) | [screenshot](lint-controls.png) |
| Strict-build negative controls | missing heading and missing-nav Page rejected | [log](strict-controls.txt) | [screenshot](strict-controls.png) |
| GitHub CI on exact latest head | all 10 checks successful | [log](ci.txt) | [screenshot](ci.png) |
| NEW P2 · minimal expected-rejection contract | RED: harness exit 1; script wrongly accepts outside file | [log](escape-minimal.txt) | [screenshot](escape-minimal.png) |
| NEW P2 · actual notebook / online Gate | RED: harness exit 1; strict build and links both exit 0 | [log](escape-real.txt) | [screenshot](escape-real.png) |
| NEW P2 · repeated and one-variable controls | cause confirmed; three repeats reproduce | [log](escape-controls.txt) | [screenshot](escape-controls.png) |
| NEW P2 · actual public destination | HTTP 404 at capture time | [log](live-destination.txt) | [screenshot](live-destination.png) |
| NEW P2 · Chromium URL and click | resolves to /README.md, outside publication path | [log](browser-dom.txt) | [screenshot](browser-dom.png) |
| Cached tool versions / archive checksums | workflow binary pins match | [log](tool-versions.txt) | [screenshot](tool-versions.png) |
| Pinned source integrity | clean; diff check passed | [log](integrity.txt) | [screenshot](integrity.png) |
| Independent Spec probes | minimal unmodified script and real notebook with HTTP disabled reproduce | [log](spec-probe.txt) | [screenshot](spec-probe.png) |

## Actual built notebook

[Rendered notebook with the fixture link](escape-notebook-rendered.png) · [After following it](escape-browser-destination.png) · [DOM assertions](browser-dom.txt).

The browser screenshots are a local replay of actual generated build files at the configured site origin. They are labelled as a replay, not a live GitHub Pages response. The real public URL was separately requested in `live-destination.txt`.

## Preserved environment and harness attempts

These are documented limitations/corrections, not additional PR findings. The successful reruns above are the evidence for the corresponding baseline claims.

| Attempt | Raw output | Screenshot |
| --- | --- | --- |
| Notebook blocked from opening a local kernel socket in the restricted sandbox | [log](notebooks-sandbox-attempt.txt) | [screenshot](notebooks-sandbox-attempt.png) |
| 404 probe initially included sandbox HTTP errors; online rerun isolates the intended failure | [log](404-coverage-sandbox-attempt.txt) | [screenshot](404-coverage-sandbox-attempt.png) |
| Diagnosis harness initially expected a filename absent from lychee's summary output | [log](escape-controls-harness-attempt.txt) | [screenshot](escape-controls-harness-attempt.png) |

Fixtures, scripts, screenshot mapping (`screenshots.json`), raw output, source diff and SHA-256 manifest are stored alongside this index. No source fix or merge is claimed. README unaffected in this review-only round; the implementation PR already updates README.
