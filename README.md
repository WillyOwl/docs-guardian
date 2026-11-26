# docs-guardian

docs-guardian is tooling that catches documentation that has fallen out of step with the code it describes, before readers do. It guards a separate **Guarded Project**, [tinyml](tinyml/): a tiny linear-regression library with a docs site, kept deliberately small so it can be broken on purpose.

Three components are built: the **snippet runner**, a Gate that fails a pull request when a Snippet breaks; the **drift check**, an Advisory check that comments on a pull request with the Pages its API Changes affect; and **lint · links · strict build**, a Gate on tinyml's Pages' style, links and site build. The health bot comes next; see [docs/architecture.md](docs/architecture.md).

## What runs today

- **Snippet runner** (`docs-guardian snippets`): runs each Markdown Page's `python` Snippets in order, one Page per process, each in an empty folder with a timeout. Snippets run with the Python that runs docs-guardian, so the Guarded Project must be installed in the same environment. A failure names the exact line in the Page. Mark a Snippet with `<!-- docs-guardian: skip -->` on the line above its fence to skip it.
- **Drift check** (`docs-guardian drift`): compares the public API under `--source` in the current checkout (uncommitted edits and new files included, files git ignores left out) with its merge base with `--base`, and writes a Drift Report listing each API Change and the Pages whose code Mentions it, plus new APIs no Page Mentions yet. It exits 0 whatever it finds: it warns, it never fails the build. A mistyped `--base`, `--source`, `--docs` or `--output` exits 2.
- **tinyml**: `load_csv`, `train_test_split`, `fit_linear`, `LinearModel.predict`, `evaluate`, and a bundled sample dataset (`tinyml.datasets.housing()`), with unit tests.
- **tinyml docs site**: home, quickstart, tutorial, notebook walkthrough and API reference, built with MkDocs + Material and published at <https://willyowl.github.io/docs-guardian/>.
- **CI** (`.github/workflows/ci.yml`): pytest on Python 3.11 and 3.14, plus a ruff lint and format check, on every pull request and push to `main`.
- **Docs tests** (`.github/workflows/docs-tests.yml`): the snippet runner on `tinyml/docs`, and the notebook via nbmake, on every pull request and push to `main`.
- **Drift check** (`.github/workflows/drift-check.yml`): posts the Drift Report as one pull request comment and rewrites it on every push. A fork's pull request, whose token cannot comment, gets the report in the job summary instead.
- **Docs lint** (`.github/workflows/docs-lint.yml`): four checks on tinyml's Pages on every pull request and push to `main`: `markdownlint` (markdownlint-cli2), `vale` (the house style in `.vale/styles/DocsGuardian`), `strict-build` (`mkdocs build --strict`, which also fails on Pages missing from the nav and links to missing headings) and `links` (lychee on the built site, external links included).
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

See the Drift Report your branch would get, as the drift-check workflow builds it:

```bash
uv run docs-guardian drift --base main --source tinyml/src --docs tinyml/docs
```

Lint tinyml's Pages and check the built site's links, as the docs-lint workflow does. markdownlint runs through `npx` (Node.js); [Vale](https://vale.sh/docs/install) and [lychee](https://lychee.cli.rs/installation/) are single binaries (CI uses Vale 3.26.0 and lychee 0.24.2):

```bash
npx markdownlint-cli2@0.24.0
vale tinyml/docs
(cd tinyml && uv run mkdocs build --strict)
lychee tinyml/site
```

Preview the docs site at <http://127.0.0.1:8000/docs-guardian/>:

```bash
cd tinyml
uv run mkdocs serve
```

## Repo layout

| Path | What it holds |
| --- | --- |
| `src/docs_guardian/` | docs-guardian, the tooling: the `docs-guardian` CLI, the snippet runner and the drift check |
| `tinyml/` | The Guarded Project: library, tests, Pages and `mkdocs.yml` |
| `tests/` | docs-guardian's own tests |
| `docs/` | Design docs: [architecture](docs/architecture.md), [ADRs](docs/adr/), agent guides |
| `.github/workflows/` | CI, docs tests, docs lint, the drift check and docs-site deploy |
| `.github/scripts/` | The drift check's comment-posting script, tested in `tests/` |
| `.vale/`, `.vale.ini`, `.markdownlint-cli2.jsonc`, `lychee.toml` | The docs-lint configuration: house style, Markdown rules and link-check rules |

## Further reading

- [GLOSSARY.md](GLOSSARY.md): the project's terms (Guarded Project, Page, Snippet, ...).
- [docs/architecture.md](docs/architecture.md): the planned design.
- [docs/adr/](docs/adr/): why it is shaped this way.
- [AGENTS.md](AGENTS.md): branching and pull request rules for contributors.
