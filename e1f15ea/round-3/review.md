# PR #12 review round 3

Reviewed source `e1f15ea6789dc0d566c3c8d997a864419529fd83` against base `d48615c3386b813d0fc6845a23e1588e3c57bf67`, covering all 10 changed files and all six commits. Source files were not changed in this review.

## Standards

No documented-standard violations or actionable heuristic smells. See the unmodified [Standards report](standards-review.md). The previously declined site URL duplication is not raised again.

## Spec

One confirmed **P2**: reject relative links that escape the published build. See the unmodified [Spec report](spec-review.md) and [independent probes](spec-probe.md). The originating architecture requires lychee to catch “Broken internal and external links” ([spec-source.md](spec-source.md), line 150).

Location: `.github/scripts/check-links.sh:20–23`, especially the input directory at line 23. The script scans the real checkout build directory. `--root-dir` handles root-relative URLs but does not constrain ordinary relative links to files in the published build.

Add this notebook Markdown cell:

```markdown
[Review unpublished repository readme](../../../../README.md)
```

At the generated notebook Page, lychee finds the checkout's existing `README.md` outside `tinyml/site/`; strict build and the real online link Gate both exit 0 (158 OK). The browser resolves the same href to `https://willyowl.github.io/README.md`, outside `/docs-guardian/`. An independent request to that exact public URL returned **HTTP 404** at capture time. The build never publishes the repository README there.

### Diagnosis

1. **Tight feedback loop:** `python /tmp/pr12-review-round3/run_checks.py escape-minimal`. One published HTML file links to a sibling unpublished HTML file. The real check script reports `1 OK`, exit 0; the expected-rejection harness exits **1**. This is intentionally red evidence of the defect, not a baseline test failure.
2. **Minimal and deterministic:** only the link and its outside target are necessary. Three repeated calls accepted it in 1 ms each. Removing only the outside target makes lychee reject it with `File not found`, exit 2.
3. **Ranked predictions shown before controls:** filesystem traversal; remap interference; excluded URL. Removing the outside target confirms the first. Removing `--remap` leaves it accepted, and output counts `1 OK`, eliminating the other explanations.
4. **Control:** copying only published files to an isolated directory makes the same relative link fail. This demonstrates a direction for a fix, but is not an implementation fix.
5. **Original-scale verification:** the actual notebook build reproduces with the unmodified script and online checking. Chromium resolves and follows the rendered link outside the configured publication path. Its 404 screenshot is an explicitly labelled local publication replay; the separate live HTTP check verifies the actual public target's 404.

Recommended change: validate relative URLs using HTTP publication semantics or restrict their resolved targets to the published build while retaining the current root-relative handling. Add a regression at `tests/test_check_links.py` using an existing sibling checkout file, plus the real notebook example.

### Dispositions

| Axis / point | Verdict |
| --- | --- |
| Standards | No points raised |
| Spec 1: relative links escape the published site | `declined: no implementation change in this review-only round; the confirmed P2 defect remains open for the PR author` |

“Declined” records the absence of a source change, as required by the repository's verdict vocabulary; the finding remains valid and open. Recommendation: address this P2 before merging.

### Existing fixes and baseline

Python 3.11 and 3.14 each pass 112 tests, with the actual lychee binary enabled so link tests do not skip. All five link-check tests pass. The original same-site URL and notebook heading failures are now correctly rejected; the valid root-relative link passes. The real built `404.html` is covered: adding a broken link only there is rejected. Twelve valid/broken URL and anchor probes, Markdownlint, Vale, strict build, Ruff, four Snippet Pages, one executed notebook, and the ten CI checks pass.

See [README.md](README.md) for per-check logs and screenshots, and [verification.md](verification.md) for commands and limitations. No temporary debugging instrumentation or regression tests were added to the source, and the source worktree is clean. Fix and fix-verification phases are not performed because the requested deliverable is a review.

Standards: **0 findings**, worst issue: none. Spec: **1 finding**, worst issue: **P2** unchecked broken relative links.
