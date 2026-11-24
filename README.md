# docs-guardian

docs-guardian is tooling that catches documentation that has fallen out of step with the code it describes, before readers do. It guards a separate **Guarded Project**, [tinyml](tinyml/): a tiny linear-regression library with a docs site, kept deliberately small so it can be broken on purpose.

The first check is built: the **snippet runner**, a Gate that runs every Snippet of every Page and fails the pull request when one breaks. The drift check and health bot come next; see [docs/architecture.md](docs/architecture.md).

## What runs today

- **Snippet runner** (`docs-guardian snippets`): runs each Markdown Page's `python` Snippets in order, one Page per process, each in an empty folder with a timeout. Snippets run with the Python that runs docs-guardian, so the Guarded Project must be installed in the same environment. A failure names the exact line in the Page. Mark a Snippet with `<!-- docs-guardian: skip -->` on the line above its fence to skip it.
- **tinyml**: `load_csv`, `train_test_split`, `fit_linear`, `LinearModel.predict`, `evaluate`, and a bundled sample dataset (`tinyml.datasets.housing()`), with unit tests.
- **tinyml docs site**: home, quickstart, tutorial, notebook walkthrough and API reference, built with MkDocs + Material and published at <https://willyowl.github.io/docs-guardian/>.
- **CI** (`.github/workflows/ci.yml`): pytest on Python 3.11 and 3.14, plus a ruff lint and format check, on every pull request and push to `main`.
- **Docs tests** (`.github/workflows/docs-tests.yml`): the snippet runner on `tinyml/docs`, and the notebook via nbmake, on every pull request and push to `main`.
- **Deploy** (`.github/workflows/deploy.yml`): builds the site with `mkdocs build --strict` and publishes it to GitHub Pages on every push to `main`.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/). One `uv sync` installs docs-guardian, tinyml and the docs tooling, as a uv workspace:

```bash
uv sync
```

Run the tests and lint:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Run every Snippet and notebook in tinyml's Pages, as the docs-tests workflow does:

```bash
uv run docs-guardian snippets tinyml/docs
uv run pytest --nbmake tinyml/docs/notebooks
```

Preview the docs site at <http://127.0.0.1:8000/docs-guardian/>:

```bash
cd tinyml
uv run mkdocs serve
```

## Repo layout

| Path | What it holds |
| --- | --- |
| `src/docs_guardian/` | docs-guardian, the tooling: the `docs-guardian` CLI and the snippet runner |
| `tinyml/` | The Guarded Project: library, tests, Pages and `mkdocs.yml` |
| `tests/` | docs-guardian's own tests |
| `docs/` | Design docs: [architecture](docs/architecture.md), [ADRs](docs/adr/), agent guides |
| `.github/workflows/` | CI, docs tests and docs-site deploy |

## Further reading

- [GLOSSARY.md](GLOSSARY.md): the project's terms (Guarded Project, Page, Snippet, ...).
- [docs/architecture.md](docs/architecture.md): the planned design.
- [docs/adr/](docs/adr/): why it is shaped this way.
- [AGENTS.md](AGENTS.md): branching and pull request rules for contributors.
