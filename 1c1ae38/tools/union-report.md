<!-- docs-guardian:drift-report changes=2 drift-pages=2 -->
### Drift Report

Public API in this checkout, compared with its merge base with `main` (`1234567`). Advisory: this check never fails the build.

2 API Changes; Drift on 2 Pages.

| API | Change | Pages that Mention it |
| --- | --- | --- |
| `fit` | `(x: int \| str)` → ``(x: int \| str, sep='`')``, `(y)` | `quick\|start.md:2`, `walk.ipynb (cell 3, line 1)` |
| `old` | removed | none |
