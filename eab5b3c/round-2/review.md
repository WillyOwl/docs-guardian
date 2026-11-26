# PR #12 review round 2

Reviewed `eab5b3ca743838c270066d5c3f72f9a13582832a` against `d48615c3386b813d0fc6845a23e1588e3c57bf67` (`main`). Diff: `git diff d48615c3386b813d0fc6845a23e1588e3c57bf67...HEAD`, 10 changed files. This round reviews the full PR plus the two fixes from round 1. Source remains unchanged.

## Standards

The independent [raw Standards report](standards-review.md) found **0 documented-standard violations** and **1 low-priority heuristic**: the site deployment URL is duplicated in `tinyml/mkdocs.yml:3`, `.github/scripts/check-links.sh:8`, and `tests/test_check_links.py:48`. Updating the deployment configuration alone could leave the check and its tests exercising an old URL. This is a possible Shotgun Surgery smell, not a present correctness failure or a documented-rule violation.

Disposition: `declined: optional follow-up; the current URL is consistent and this review-only round makes no source change`. The suggestion is retained separately from the Spec finding.

## Spec

The independent [raw Spec report](spec-review.md) found **one P2**:

**Resolve valid root-relative site links before checking the build** — `.github/scripts/check-links.sh:11–13`. The pre-change specification (`docs/architecture.md:146`) says lychee catches “Broken internal and external links.” The wrapper only remaps full HTTPS URLs, without supplying the web-root context for `/docs-guardian/...` URLs. A Page with `[Review valid root-relative quickstart](/docs-guardian/quickstart/#quickstart)` passes the real strict MkDocs build, and its generated destination and heading exist, but `check-links.sh` fails with exit 2 and `Cannot resolve root-relative link ... provide a root dir`.

This is a false positive that blocks a valid documentation change. Browser replay of the actual generated site at its configured deployment origin confirms that clicking this link reaches the visible `h1#quickstart` heading. The replay serves local build files through Playwright request routing; it is not a screenshot of the live deployment.

Suggested correction: resolve site-root URLs against the current build while honoring the `/docs-guardian/` deployment prefix, and cover both existing and missing root-relative targets at the existing `tests/test_check_links.py` seam. Passing the bare site directory as `--root-dir` is insufficient unless the deployment prefix is handled too.

Disposition: `declined: no implementation change in this review-only round; the confirmed P2 remains open for the PR author`. This verdict records the decision not to change source; it does not dismiss the defect.

## Diagnosis

No specific broken symptom was reported by the user, so this review began with executable specification checks. Diagnosis phases apply to the new failed contract, rather than treating a review request as a request to fix source.

1. **Feedback loop:** `python3 tools/reproduce_root_relative.py`. It calls the real script with one valid root-relative link, expects exit 0, and returns 1 on the current PR. `root-relative-minimal.txt` records two deterministic failures, each in milliseconds. The loop can turn green once the script accepts this valid link.
2. **Reproduce and minimize:** the fixture has only an input `index.html` with one link and its existing `quickstart/index.html` destination. No notebook, fragment, external request, or MkDocs setup is required. The full build reproduction is retained separately in `root-relative-actual.txt` with its source patch.
3. **Ranked predictions, communicated before controls:** (1) missing site-root context: supplying the deployed mount as `--root-dir` should pass; (2) directory-index resolution failure: a root context alone should still fail; (3) remap interference: retaining the HTTPS remap should still fail even with a root context.
4. **One-variable control:** `root-relative-controls.txt` retains the config, HTTPS remap, href and index settings. Adding only `--root-dir` with a `/docs-guardian/` mount changes exit 2 to exit 0. A missing root-relative destination still fails. Hypothesis 1 is supported; 2 and 3 are falsified. This control is not a committed fix.
5. **Regression seam:** `tests/test_check_links.py` already runs the actual wrapper on built HTML and is the correct seam for this failure. Its four existing tests pass but omit root-relative URLs. The review fixture is stored as evidence; no source test or fix is committed in this review-only round.
6. **Cleanup and limits:** the tracked source is unchanged and the pinned worktree is clean (`integrity.txt`). MkDocs' untracked `.cache/` was moved outside source into a clearly named generated-cache directory. All scratch mutations remain under the review directory and are labeled as fixtures. No debug instrumentation was added. The new reproduction remains red, so this report does not claim the bug has been fixed.

## Prior-round findings

- Same-site absolute URLs: **fixed in `5fb7dd1`**, verified on current head. Adding the original dead URL to the real home Page passes strict build but now fails the link Gate with `File not found`, exit 2 (`same-site-fixed.txt`). Valid new same-site targets pass the small-site tests.
- Notebook anchors: **fixed in `5fb7dd1`**, verified on current head. Appending the original missing-anchor cell to the real notebook passes strict build but now fails the link Gate with `Cannot find fragment`, exit 2 (`notebook-anchor-fixed.txt`). Valid anchors pass.
- Notebook prose linting: prior `declined` scope interpretation remains unchanged; Markdown-only linting is documented.

## Validation

- Full pytest suite: **111 passed on Python 3.11.15**; **111 passed on Python 3.14.6**. Lychee was supplied so the three binary-dependent tests ran.
- Link rule tests: **4 passed**.
- Markdownlint 0.24.0, Vale 3.26.0, strict build and Ruff pass.
- Real online link Gate: **143 OK, 0 errors**. The initial sandbox network failure is preserved as `links-sandbox.txt`; the network-enabled retry passes. This environment issue is not a PR finding.
- All **10 CI checks succeed** on the exact reviewed head; this is a fresh status capture, not a new CI run.
- `boundary-probes.txt` and `root-relative-minimal.txt` intentionally end in harness exit 1 because the new contract remains broken. Negative fixtures in the other harnesses expect underlying link-check exit 2 and report harness exit 0 when that rejection is correct.
- Every saved `.txt` log has a fresh same-name `.png` and `.html`; browser Page screenshots, fixtures, capture tools, and reproduction steps accompany them. Initial integrity output records only the generated cache before cleanup; final integrity is clean.

Standards: **0 hard violations, 1 low-priority heuristic**; worst within this axis: duplicated deployment URL maintenance risk. Spec: **1 confirmed P2**; worst within this axis: rejection of valid root-relative reader links. Recommendation: address the Spec P2 before merging.
