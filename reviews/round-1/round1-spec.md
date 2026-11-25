# Review round 1 — Spec axis (subagent report, verbatim)

Reviewed: uncommitted diff on feat/drift-check against main 6af3ec1.

Spec review — uncommitted feat/drift-check. 74 tests pass; `docs-guardian drift` on tinyml → "No API Changes", exit 0. Probes in throwaway repos under scratchpad/drift-specprobe/.

**(a) Missing / partial**
- "A second push to that PR edits the same comment, not a new one": the workflow has no `concurrency:` group. Two quick pushes → both runs find no comment and both POST (duplicate comments), or an older run finishes last and overwrites with a stale report. Add `concurrency: drift-${{ github.event.pull_request.number }}` with `cancel-in-progress: true`.
- "Demo PR adds a parameter to evaluate; bot comments with the right pages": not verifiable until pushed — still an open done-criterion.

**(b) Scope creep**
- Marker line carries counts (`changes=N drift=N`) parsed by the workflow via `sed` — spec only asks for a hidden marker; harmless.
- Private-module exclusion (author decision) is risky: a package defining everything in `_impl.py` and re-exporting from `__init__.py` gets zero visible API. tinyml is fine today (public functions live in public modules).
- Other author decisions look sound: `pull_request` (not `_target`), warn-on-read-only-token, counting Skipped Snippets.

**(c) Implemented but looks wrong**
- ADR 0001 "the drift check warns, never fails": confirmed crashes (step fails → red check) on a syntax error in any source file (`SyntaxError`), a non-UTF-8 Page (`UnicodeDecodeError`), and a nonexistent base ref (`CalledProcessError`). Malformed notebook JSON and a source root outside the git repo also raise. `_run_drift`'s docstring says errors "still raise", contradicting the ADR. Needs `continue-on-error` on the build step or catching in code.
- Q12 "key by public name across the whole package": `package_api` uses `api.update` — when two modules define the same name, one silently shadows the other. Confirmed: changing `evaluate` in `m.py` while `n.py` also defines `evaluate` reports "No API Changes". Same for overloads (last definition wins).
- Q13 "methods matched as `.predict(`": code uses `\.predict\b` (no paren). Top-level names use bare `\b`, so a function `fit` also matches `model.fit(x)` — over-reporting.
- Q18 "`__init__`'s signature counts as the class's own signature": a class inheriting `__init__` shows `()` — near the accepted dataclass gap but broader.
- Q27/Q28: comment posted whenever `changes != 0`, even with no Drift — a reasonable reading of "nothing to report"; README/architecture state it correctly.
- Workflow marker matching: `startswith(marker)` doesn't filter by author; a human comment beginning with the marker gets selected, the PATCH fails, and the report never updates.
- Large reports: GitHub rejects comment bodies > 65,536 chars (422); the workflow then prints a misleading "read-only token, e.g. a fork" warning.

README updated; docs changes are consistent with behaviour.
