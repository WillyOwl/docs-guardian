# PR #12 review round 2 evidence

Reviewed **eab5b3ca743838c270066d5c3f72f9a13582832a** against **d48615c3386b813d0fc6845a23e1588e3c57bf67**.

- [Review and diagnosis](review.md)
- Independent raw reports: [Standards](standards-review.md), [Spec](spec-review.md)
- [Verification steps](verification.md)
- [Capture and reproduction tools](tools/) · [mutation fixtures](fixtures/)
- [Screenshot inventory](screenshots.json) · [artifact hashes](manifest.json)

New finding: **P2, valid root-relative links are rejected**. Prior two P2 findings are verified fixed. Baseline: 111 tests pass on each of Python 3.11 and 3.14; 4 link tests pass; Markdownlint, Vale, strict-build, online links and Ruff pass; all 10 CI checks succeed on the pinned head.

`root-relative-minimal` and `boundary-probes` are intentionally red. `links-sandbox` is the original network-restricted attempt, superseded by passing `links`; `integrity-initial` records only a generated cache, superseded by clean `integrity`. Diagnosis controls demonstrate a possible correction but are not source fixes.

Actual built Page screenshots, served locally through Playwright request routing at the configured deployment origin (not live-site captures): [source Page](root-relative-rendered.png), [working destination after click](root-relative-destination.png), [DOM assertion](browser-dom.txt).

| Captured run | Raw output | Fresh image |
| --- | --- | --- |
| `boundary-probes.txt` | [log](boundary-probes.txt) | [screenshot](boundary-probes.png) |
| `browser-dom.txt` | [log](browser-dom.txt) | [screenshot](browser-dom.png) |
| `ci.txt` | [log](ci.txt) | [screenshot](ci.png) |
| `integrity-initial.txt` | [log](integrity-initial.txt) | [screenshot](integrity-initial.png) |
| `integrity.txt` | [log](integrity.txt) | [screenshot](integrity.png) |
| `link-regressions.txt` | [log](link-regressions.txt) | [screenshot](link-regressions.png) |
| `links-sandbox.txt` | [log](links-sandbox.txt) | [screenshot](links-sandbox.png) |
| `links.txt` | [log](links.txt) | [screenshot](links.png) |
| `markdownlint.txt` | [log](markdownlint.txt) | [screenshot](markdownlint.png) |
| `notebook-anchor-fixed.txt` | [log](notebook-anchor-fixed.txt) | [screenshot](notebook-anchor-fixed.png) |
| `pytest-311.txt` | [log](pytest-311.txt) | [screenshot](pytest-311.png) |
| `pytest-314.txt` | [log](pytest-314.txt) | [screenshot](pytest-314.png) |
| `root-relative-actual.txt` | [log](root-relative-actual.txt) | [screenshot](root-relative-actual.png) |
| `root-relative-controls.txt` | [log](root-relative-controls.txt) | [screenshot](root-relative-controls.png) |
| `root-relative-minimal.txt` | [log](root-relative-minimal.txt) | [screenshot](root-relative-minimal.png) |
| `ruff.txt` | [log](ruff.txt) | [screenshot](ruff.png) |
| `same-site-fixed.txt` | [log](same-site-fixed.txt) | [screenshot](same-site-fixed.png) |
| `spec-probes/anchor-bad.txt` | [log](spec-probes/anchor-bad.txt) | [screenshot](spec-probes/anchor-bad.png) |
| `spec-probes/anchor-valid.txt` | [log](spec-probes/anchor-valid.txt) | [screenshot](spec-probes/anchor-valid.png) |
| `spec-probes/relative-bad-anchor.txt` | [log](spec-probes/relative-bad-anchor.txt) | [screenshot](spec-probes/relative-bad-anchor.png) |
| `spec-probes/relative-valid.txt` | [log](spec-probes/relative-valid.txt) | [screenshot](spec-probes/relative-valid.png) |
| `spec-probes/root-relative-mkdocs/links.txt` | [log](spec-probes/root-relative-mkdocs/links.txt) | [screenshot](spec-probes/root-relative-mkdocs/links.png) |
| `spec-probes/root-relative-mkdocs/strict-build.txt` | [log](spec-probes/root-relative-mkdocs/strict-build.txt) | [screenshot](spec-probes/root-relative-mkdocs/strict-build.png) |
| `spec-probes/root-relative-valid.txt` | [log](spec-probes/root-relative-valid.txt) | [screenshot](spec-probes/root-relative-valid.png) |
| `spec-probes/same-site-bad-anchor.txt` | [log](spec-probes/same-site-bad-anchor.txt) | [screenshot](spec-probes/same-site-bad-anchor.png) |
| `spec-probes/same-site-missing.txt` | [log](spec-probes/same-site-missing.txt) | [screenshot](spec-probes/same-site-missing.png) |
| `spec-probes/same-site-valid.txt` | [log](spec-probes/same-site-valid.txt) | [screenshot](spec-probes/same-site-valid.png) |
| `strict-build.txt` | [log](strict-build.txt) | [screenshot](strict-build.png) |
| `tool-versions.txt` | [log](tool-versions.txt) | [screenshot](tool-versions.png) |
| `vale.txt` | [log](vale.txt) | [screenshot](vale.png) |
