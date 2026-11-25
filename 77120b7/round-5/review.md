# PR #11 code review, round 5

Reviewed commit: `77120b704a46df07b8fa18c418863523e26e9cd6`.
Base: `origin/main` (`6af3ec1`). Review date: November 25, 2026 UTC.

Result: two confirmed P2 correctness findings. No implementation changes were made. Both findings remain open and await fixes. All new probes are stored only on the evidence branch.

## F1 — P2: collect every constructor signature, not just the first overload

Location: `src/docs_guardian/drift.py:74-76`.

`public_api` uses `next(...)` to select the first `__init__` in each class, then excludes every `__init__` from the public-method loop. For a valid class with overloaded constructors, every later overload and the runtime implementation signature are therefore discarded. Changing the second overload from `value: str` to `value: bytes` produces identical before/after APIs and `No API Changes.`, even when a Page explicitly mentions `Estimator("sample")`. Adding a keyword-only argument to the implementation is also invisible.

This contradicts the PR's documented handling of whole signature sets for repeated names and overloads. It is separate from the accepted dataclass/inherited-constructor gap: every constructor in this reproduction is defined directly in the class. Collect the signatures of all directly defined `__init__` nodes into the class's signature set, and use `()` only if none exists.

Evidence: the first two tests in `test_review_round5.py` fail on both supported interpreters. Their captured API dictionaries contain only `(self, value: int) -> None`. The non-overloaded-constructor control passes.

Disposition: confirmed; awaiting fix.

## F2 — P2: retain package names when finding Mentions of removed APIs

Location: `src/docs_guardian/drift.py:507-508`.

Package prefixes are discovered solely from immediate directories in the current checkout that still contain `__init__.py`. If the PR removes a whole package, the API collector correctly detects its removed `fit`, but its package name is no longer passed to `find_mentions`. The bare-name pattern deliberately rejects names after a dot, so the unchanged Page code `pkg.fit(1)` is missed. The CLI reports `1 API Change; no Drift` with `| fit | removed | none |` instead of pointing to `guide.md:3`.

The fixture retains an independent public package under `src`, so the source root remains valid. Removing only the function while retaining `pkg/__init__.py` passes, isolating the cause to package discovery. The same filter misses qualified Mentions for PEP 420 namespace packages (`pkg/ops.py` without `pkg/__init__.py`); changing `fit` reports no Drift even for inline code `pkg.ops.fit(1)`.

Derive package prefixes from the source trees being compared, including the merge-base side for removals, and account for namespace packages. Preserve the existing exclusion of unrelated object attributes such as `model.fit`.

Evidence: the third and fourth tests in `test_review_round5.py` fail on both supported interpreters. Controls for an existing regular package and removal of only a function pass.

Disposition: confirmed; awaiting fix.

## Verification

| Check | Result |
| --- | --- |
| Existing full suite, Python 3.11.15 | 103 passed |
| Existing full suite, Python 3.14.6 | 103 passed |
| Independent probes, Python 3.11.15 | 4 failed, 3 controls passed; reproduce F1 and F2 |
| Independent probes, Python 3.14.6 | 4 failed, 3 controls passed; reproduce F1 and F2 |
| Ruff lint and format | Both pass |
| Markdown Snippets | All 4 Pages pass |
| Notebook execution | 1 passed after authorized retry outside socket-restricted sandbox |
| Strict docs build | Pass |
| Drift on this PR's unchanged tinyml API | No API Changes; exit 0 |
| GitHub CI at reviewed head | All six checks pass |
| Reviewed checkout | Clean; `git diff --check` passes |

All outputs include the exact command, source checkout, timestamp and exit status. Every cited check has a fresh Chromium screenshot of its complete saved output alongside its raw log and source HTML. `screenshots.json` records image/log hashes and viewports. This is a browser log viewer, not a screenshot of a terminal or a GitHub page.

The reviewed detached worktree is unchanged. Existing Python environments were reused with `PYTHONPATH` explicitly selecting the reviewed checkout. `environment.txt` records import locations and versions. The first notebook run failed solely because the sandbox blocks local sockets; its original output and screenshot are preserved as `notebooks-sandbox.*`. The authorized retry passed.

A live bot's first POST and subsequent PATCH remain unverified; this review does not create a demo PR or mutate a bot comment. Existing tests exercise the real posting script with a stubbed `gh`. The documented private-module re-export and generated/inherited-constructor limitations were not reported as defects.

README updated by the PR; README unaffected by this evidence-only review.
