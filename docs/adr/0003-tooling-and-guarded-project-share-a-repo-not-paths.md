# docs-guardian and the Guarded Project share a repo, not paths

docs-guardian (`src/docs_guardian/` at the repo root, one CLI) and the Guarded Project (a self-contained `tinyml/` folder with its own `pyproject.toml`, `src/`, `docs/` and `mkdocs.yml`) live in one repo so that demo PRs can break code and docs together. The root `docs/` belongs to docs-guardian (ADRs, agent docs) and is never published or scanned as Pages. Every docs-guardian command still takes the docs root and the source root as arguments, and nothing in docs-guardian imports tinyml or hard-codes its paths. That keeps the "docs in a separate repo from code" setup common at docs teams one checkout away rather than a rewrite.

## Considered Options

- **Loose `tools/*.py` scripts** (the original build guide). They are quicker to start, but they blur the tooling and the thing it guards into one codebase.
- **Separate repos**. This is the honest end state, but cross-repo demo PRs cost too much in a three-day build.
