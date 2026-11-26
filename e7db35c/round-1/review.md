# PR #12 review round 1

Reviewed head: `e7db35cdf9cd8c70e63dc592d821f9243875dc76`.
Fixed base: `d48615c3386b813d0fc6845a23e1588e3c57bf67`.
Diff: `git diff d48615c3386b813d0fc6845a23e1588e3c57bf67...e7db35cdf9cd8c70e63dc592d821f9243875dc76`.
Commits: `15c5864`, `e7db35c`. All 8 changed files reviewed.

Spec source: pre-change `docs/architecture.md`, Lint · links · strict build (Gate), plus the PR's documented behavior. There are no issue references in the commits and the repository's GitHub issue list is empty.

## Standards

No documented-standard breaches or actionable smell findings. See the independent [raw report](standards-review.md).

## Spec

The independent [raw report](spec-review.md) raises three points, retained in its original order below. Two are confirmed by running the actual configured tools.

1. **[P2] Validate same-site absolute URLs against the local build** — `lychee.toml:14–16`. Appending `[Review missing page](https://willyowl.github.io/docs-guardian/pr12-review-missing-page/)` to `tinyml/docs/index.md` makes neither strict-build nor the original online lychee command fail. The URL remains in the generated HTML; its local destination does not exist. The blanket exclusion makes lychee report one more excluded link. Mapping the same URL to `file://<checkout>/tinyml/site/...` immediately produces `File not found` and exit 2. Relative links work, but that does not validate these absolute links. Suggested fix: remap the site's public prefix to the current local build instead of excluding it, preserving validation of newly added Pages before deployment.
   - Evidence: [online reproduction](same-site-url-online.txt), [controls](same-site-controls.txt), and matching PNG screenshots.
   - Code-change verdict: **declined: this review-only round reports the confirmed defect for the PR author; no implementation fix was requested or pushed. The finding remains open.**

2. **[P2] Enable fragment checking for notebook links** — `lychee.toml:5–6`; related `tinyml/mkdocs.yml:40–41`. A single notebook Markdown cell containing `[Review missing heading](#pr12-review-missing-heading)` passes both strict-build and the original online lychee command. It still reproduces when the notebook is reduced to that single cell. The rendered HTML contains the link but no matching target ID. The same fragment in a Markdown Page makes strict-build fail, demonstrating the notebook renderer's separate path. Changing only the lychee invocation to `--include-fragments=anchor-only` catches the notebook link with `Cannot find fragment` and exit 2; a valid notebook anchor still passes. Suggested fix: enable `include_fragments = "anchor-only"` in the pinned lychee configuration and retain a regression at the built-site seam.
   - Evidence: [online reproduction](notebook-anchor-online.txt), [minimized reproduction](notebook-anchor-minimal.txt), [controls](anchor-controls.txt), [browser DOM check](browser-dom.txt), and matching PNG screenshots.
   - Code-change verdict: **declined: this review-only round reports the confirmed defect for the PR author; no implementation fix was requested or pushed. The finding remains open.**

3. **Notebook prose formatting and terminology coverage** — `.markdownlint-cli2.jsonc:9`, `.vale.ini:6–7`.
   - Verdict: **declined: the PR explicitly documents that Markdownlint and Vale read Markdown only and assigns notebook coverage to strict-build and links. The earlier architecture does not explicitly require extracting notebook prose into either linter. This is an acknowledged scope choice, not a confirmed regression in that chosen scope.** No additional failure claim is made for this point.

Standards: 0 findings. Spec: 3 raw points; 2 confirmed P2 findings remain open, 1 declined scope interpretation.

## Validation

Baseline: 107 pytest tests pass on Python 3.14.6; Markdownlint 0.24.0, Vale 3.26.0, strict MkDocs build, lychee 0.24.2, Ruff lint and formatting pass. All 10 existing GitHub CI checks are successful on the reviewed SHA. These checks do not contain the two mutation cases above.

Reproductions return harness exit 1 because the assertion expects the Gate to reject broken documentation; both underlying commands incorrectly return 0. Control runs return harness exit 0 after verifying that enabling fragment checks or remapping the public URL catches the deliberately broken destination. These controls are diagnostic experiments, not a claim that the PR contains a fix.

## Diagnosis workflow

- Tight loops were established and run before root-cause probes: `python3 /tmp/pr12-review/run_checks.py notebook-anchor` and `python3 /tmp/pr12-review/run_checks.py same-site-url`.
- Each mutation is one bad link; the notebook case was further minimized to a single Markdown cell. Original and mutated SHA-256 values and diffs are captured before running checks.
- Ranked predictions were presented before controls: disabled fragments, same-site exclusion, or a fixture that did not render. DOM assertions and the one-variable controls establish the first two and rule out the third.
- Phase 5 (source fix and committed regression) is intentionally outside this review-only request. The harness is preserved at the actual built-site integration seam for the author to turn into regression coverage.
- No debug instrumentation or source edits were added to the PR. Mutation copies and the harness are retained in a clearly marked review workspace and the evidence branch. The source integrity log records the clean reviewed worktree. MkDocs' generated root `.cache/` was moved to a separate temporary output directory before the clean-worktree check.
