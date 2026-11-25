# PR #11 code review — round 2

Reviewed commit: `39c7d290bbb0a982e8f173d518ea5b03fe23b84c`.
Base: `6af3ec1c790f170e064659a1f23ae2e1f6008c04` (`origin/main`).
Recommendation: address the five confirmed findings before merging.
Scope: all six changed files, the glossary, ADR 0001, ADR 0003, existing tests,
and the previous review. No implementation commits were made in this round.
All findings below remain open.

## F1 — [P2] Preserve complete signatures when collecting overloads

Location: `src/docs_guardian/drift.py:107–109`, also `_add` at lines 39–42.

`SIGNATURE_SEPARATOR` is ` | `, which is also the spelling of Python union
annotations and bitwise defaults after `ast.unparse`. `package_api` splits
every signature on this separator, then `_add` sorts and deduplicates the
pieces. This changes their meaning and can erase real API Changes.

Reproduction: change
`def convert(value: int | str | bytes) -> float | bool | None: ...`
to `def convert(value: int | bool | bytes) -> float | str | None: ...`.
The accepted parameter and return types both change, but the CLI reports
`changes=0` and `No API Changes.` The affected Page is consequently omitted.

Keep complete signatures as structured sets/lists through collection and
comparison; join them only when displaying them. A different printable
separator alone does not solve the lossless representation requirement.

Evidence: `test_union_annotation_changes_are_reported` in
`review-regressions.txt`; reproduction source in `test_review_regressions.py`.
Disposition: confirmed; pending implementation fix.

## F2 — [P2] Escape pipes in Markdown table cells

Location: `src/docs_guardian/drift.py:392–394`.

The report inserts annotations and defaults directly into a pipe-delimited
Markdown table. Inline-code backticks do not protect `|` in GitHub tables.
For a change from `(x: int | str)` to `(x: int | str, y=0)`, GitHub splits the
signature into extra cells and drops the actual Pages cell, including
`quickstart.md:2`. Thus an ordinary union annotation can hide the locations
that the Drift Report is meant to provide. This is independent of F1: a
correctly detected change still renders incorrectly.

Escape cell content for GitHub Markdown before constructing the table;
cover signature/default strings as well as Page paths.

Evidence: `test_union_signature_keeps_the_pages_table_cell`; `union-report.md`
was also sent to GitHub's actual `POST /markdown` endpoint with `mode=gfm`.
`github-table-render.txt` contains the returned HTML, which has no
`quickstart.md:2`; `union-report-rendered.png` shows input and actual output.
Disposition: confirmed; pending implementation fix.

## F3 — [P2] Treat malformed notebook structure as unreadable content

Location: `src/docs_guardian/drift.py:230–235`, exception handling at 279.

The decoder assumes valid notebook field types. A Page containing valid JSON
`{"cells": null}` raises `TypeError` when enumerated. Likewise,
`{"cells": [{"cell_type": "code", "source": [1]}]}` raises `TypeError` in
`"".join(source)`. The surrounding handler catches JSON decoding errors and
`AttributeError` but not these type errors, so the CLI exits through an
uncaught exception instead of writing an unreadable-file note. This violates
the content-error behavior promised by ADR 0001 and this PR's documentation.

Validate notebook field types or handle the structural parsing failure and
append the Page to the unreadable list. Preserve exit 0 for content errors.

Evidence: `test_malformed_notebook_is_advisory` in `review-regressions.txt`
shows the end-to-end CLI stack trace for `{"cells": null}`.
Disposition: confirmed; pending implementation fix.

## F4 — [P2] Handle a failed comment lookup as Advisory

Location: `.github/workflows/drift-check.yml:57–59`.

Only the final POST/PATCH is protected by an `if`. The earlier `gh api`
comment-list request is an unguarded assignment containing a pipeline.
GitHub Actions runs this script with `bash -e -o pipefail`; a lookup failure
(for example HTTP 503) therefore exits the step immediately with status 1,
before the intended warning handler. The report has already reached the job
summary, but the Advisory check still turns red.

Guard the lookup itself and emit a warning with a successful exit, as the
workflow already does for a failed POST/PATCH.

Evidence: `test_comment_lookup_failure_is_advisory` executes the unmodified
posting script with the same Bash flags and a mocked `gh` returning HTTP 503.
It exits 1 without a warning. `workflow-mocked.txt` separately confirms the
five existing paths (skip, POST, PATCH, clear an old report, POST 403 warning).
These are local mocked checks; they do not demonstrate a live bot posting.
Disposition: confirmed; pending implementation fix.

## F5 — [P2] Locate inline code spans independently of matching prose

Location: `src/docs_guardian/drift.py:221–225`.

The code searches `token.content` for `child.content`, starting from the end
of the previous code span. Ordinary text children do not advance the cursor.
For this two-line paragraph:

```markdown
We evaluate the model.
Then call `evaluate`.
```

the search finds the plain-text `evaluate` on line 1, although the Mention is
the inline code span on line 2. The report points readers at the wrong line.
Repeated names and normalized multiline spans have the same underlying risk.

Track span positions in the Markdown source rather than searching the full
paragraph for the decoded code text, accounting for prior text tokens and
code delimiters.

Evidence: `test_inline_code_location_skips_preceding_prose` reports
`guide.md:1` where `guide.md:2` is required.
Disposition: confirmed; pending implementation fix.

## Verification results and limits

- Existing tests: 82 passed on Python 3.14.6 and 82 passed on Python 3.11.15.
- Ruff check and format check: passed; 25 files formatted.
- Snippet runner: all 4 Markdown Pages passed.
- Notebook: 1 passed. Initial sandbox attempt could not create a Jupyter
  socket; rerunning outside the sandbox passed. Both outputs are retained.
- Current branch's Drift Report: no API Changes, exit 0.
- Additional regression probes: 5 failed as expected, reproducing F1–F5.
  These probes live only on the evidence branch and are not existing suite failures.
- Workflow happy/error paths: 5 mocked cases passed. Live initial posting and
  rewriting remain unverified; the previous review's demo limitation remains.
- F2 was independently verified against GitHub's Markdown rendering endpoint.

Each cited command output has a fresh Chromium screenshot in this directory.
See `verification.md` for commands, environment, and screenshot provenance.
