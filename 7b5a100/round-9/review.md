# Code review: PR #11, round 9

Reviewed commit: `7b5a100481ec7a078551d307325c3f422f48793b`.
Base: `origin/main`, `6af3ec1`. Source: clean detached worktree at
`/tmp/pr11-review-round9/source`.

## Findings

All four findings are P2. F4 is new in this round. F1–F3 confirm issues already
described in the round-7 discussion; the fixes named there are absent from the
current remote PR head. These three confirmations are not presented as new bugs.
No source fixes were made.

### F4: allow the removal of the last Python module to produce a report

Location: `src/docs_guardian/drift.py:511–512`.

The checkout-only validation runs before the merge-base source is read. Delete
the last tracked Python module under a correctly configured source directory,
leave the directory and a Page that Mentions its public API, and the CLI returns
2 with `no Python files under src`. It produces no Drift Report. The workflow's
report step therefore fails before publishing the removed API and affected Page.
This is a source-content change, rather than a mistyped path, and should remain
Advisory under ADR 0001. Validate the source against both revisions so that a
nonempty base and empty checkout can be compared. A control deleting one module
while another remains does produce the expected removal and Page.

Evidence: [reproduction](f4-reproduction.txt), [screenshot](f4-reproduction.png),
`test_f4_removing_the_last_module_reports_removals_and_stays_advisory`.
Verdict: unresolved at the reviewed commit; fix recommended.

### F1: resolve guarded module aliases when matching Mentions

Location: `src/docs_guardian/drift.py:212–215`.

With `import tinyml as tm` followed by `tm.fit_linear(X, y)`, removing
`fit_linear` reports the API removal but says `drift-pages=0` and `none` for
the Page. The pattern recognizes original package paths and bare names only.
`import tinyml.models as m` and `from tinyml import models` have the same result.
Record the Page's bindings for guarded modules, while keeping unrelated object
attributes excluded. Direct qualified references and an unrelated-object control
behave correctly. The alias is executable against the actual tinyml package.

Evidence: [reproduction](f1-reproduction.txt), [screenshot](f1-reproduction.png),
three `test_f1_module_alias_mentions_are_not_lost` cases.
Verdict: unresolved at the reviewed commit; prior round-7 finding reproduced.

### F2: include code that the configured renderer places inside admonitions

Location: `src/docs_guardian/drift.py:236–240`.

The site's `admonition` and `pymdownx.superfences` extensions render both a
Python fence and an inline code span inside `!!! note` with an indented body.
CommonMark treats that body as indented code, so neither extraction path finds
the Mention. Removing the API again yields `drift-pages=0` and `none`.
Match the configured Page syntax while preserving original line numbers and
literal fenced code. The renderer control confirms that the code is visible
to a reader. This finding concerns the new Drift Report behavior; the unchanged
snippet runner's existing limitations are not a separate finding here.

Evidence: [reproduction and renderer output](f2-reproduction.txt),
[screenshot](f2-reproduction.png), two
`test_f2_mentions_in_site_admonitions_are_not_lost` cases.
Verdict: unresolved at the reviewed commit; prior round-7 finding reproduced.

### F3: inspect inline code in notebook Markdown cells

Location: `src/docs_guardian/drift.py:259–261`.

A notebook Markdown cell containing ``Call `tinyml.fit_linear(X, y)`.``
is skipped solely because its `cell_type` is not `code`. After the function
is removed, its visible inline-code Mention is absent from the Drift Report.
The glossary defines Mentions to include inline code spans; it excludes prose,
not inline code within a notebook Page. Read Markdown cells with the Markdown
extractor, preserving their cell and line locations. A notebook code-cell
control already works, and plain prose remains excluded.

Evidence: [reproduction](f3-reproduction.txt), [screenshot](f3-reproduction.png),
`test_f3_notebook_markdown_inline_code_is_a_mention`.
Verdict: unresolved at the reviewed commit; prior round-7 finding reproduced.

## Validation

- Existing suite: 107 passed on Python 3.11.15 and 107 on Python 3.14.6.
- Independent probes: 7 failed across F1–F4, with 6 controls passed, no skips.
- Ruff lint and format checks pass; 26 files already formatted.
- Snippet runner: 4 Pages pass.
- Notebook: 1 passed after an authorized retry outside the socket-restricted
  sandbox. The original sandbox failure is retained and is not a product bug.
- MkDocs strict build passes.
- This PR's unmodified tinyml API correctly produces `No API Changes`.
- All six checks returned by `gh pr checks` pass.

Every cited run has a fresh Chromium screenshot of its complete saved output,
stored alongside commands and exit statuses. See [verification.md](verification.md)
and [screenshots.json](screenshots.json). Screenshots are browser captures of
the saved logs, not fabricated terminal output.

The real GitHub Actions bot's first POST and later PATCH remain unverified.
The existing suite exercises the posting script against a stubbed `gh` only.
README updated by the PR; README unaffected by this review and evidence upload.
