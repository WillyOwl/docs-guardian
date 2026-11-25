# Review round 1 — Standards axis (subagent report, verbatim)

Reviewed: uncommitted diff on feat/drift-check against main 6af3ec1.

**Review of feat/drift-check vs HEAD 6af3ec1** (pytest 74 pass; `ruff check` / `ruff format --check` clean)

**Documented-standard issues**

1. **ADR 0001 ("PR check stays green") — possibly hard.** `cli.py` `_run_drift` returns 0 but its docstring says "Errors … still raise." In `drift.py`, `ast.parse` raises on any `.py` file with a syntax error and `json.loads` raises on a malformed `.ipynb`; a PR containing either turns the Advisory workflow red. Decide whether these should degrade to a report line.
2. **GLOSSARY "Drift" = "A Page that Mentions an API that was removed or changed" — judgement.** In `render_report`, `drift = [c for c in gone if mentions.get(c.name)]` holds API Changes, and the marker `drift={len(drift)}` counts changes, not Pages. Visible text "2 cause Drift" is consistent with the Drift Report entry; the variable/marker field aren't.
3. **GLOSSARY "API Change" (_Avoid_: diff) — judgement.** Public function named `diff_api`; `ApiChange` docstring says "public function or method" but `public_api` also keys classes (`LinearModel` → `__init__` signature).
4. **Accuracy (docs vs code):** CLI description says "public API under --source at HEAD" and README says "at the pull request's head", but `_api_in_working_tree` reads the working tree — uncommitted edits count.
5. **Consistency with snippet runner (architecture.md):** `snippets` exits 2 on an empty folder "so a mistyped path cannot pass"; `drift` with a mistyped `--docs` silently reports no Mentions.
6. **Tests convention (`pytest.raises(match=)`):** no test covers the "unknown base branch still raises" path, `--output`, or a `.ipynb`/inline span inside `render_report`.
7. **AGENTS.md evidence:** n/a until the PR is opened — this PR is not exempt (touches code); needs draft PR, `pr<N>-review-evidence`, screenshots, "README updated" in body (README is correctly updated).
8. **Minor style:** private helpers `_git`, `_api_in_working_tree`, `_plural` lack docstrings, unlike `snippets.py`'s `_kill_process_group`.

No ADR 0003 breach: paths are arguments, no tinyml import; only the workflow hard-codes `tinyml/`.

**Baseline smells (all judgement calls)**

- **Primitive Obsession / Repeated Switches:** `kind: str` (`"added"/"removed"/"changed"`) branched on in `diff_api`, three times in `render_report`, plus `what = "removed" if change.kind == "removed" ...`. An Enum fits.
- **Primitive Obsession:** `Mention(where: str)` holds only a preformatted string — page and line are lost; `find_mentions` builds anonymous tuples `((line,), where, code)` / `((cell, line), ...)` — Data Clump.
- **Duplicated Code:** `f"{len(drift)} cause{'s' if len(drift) == 1 else ''} Drift"` hand-rolls the inverse of `_plural`; the test helper `git()` duplicates `_git`.
- **Shotgun Surgery:** the marker `'<!-- docs-guardian:drift-report'` and the `changes=` format are duplicated in `drift-check.yml` (`sed` parses the first line); changing `REPORT_MARKER` or the marker format silently breaks the workflow.
- **Divergent Change (prose):** architecture.md's signature paragraph now also carries CLI usage and workflow posting behaviour; a separate paragraph would read better.
- **Redundant conversion:** `Path(docs_root)`/`Path(source_root)` re-wrap arguments already typed `Path`.
