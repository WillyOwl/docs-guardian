# MkDocs 1.6 + Material, pinned, despite maintenance mode

The Guarded Project's site is built with MkDocs 1.6 and Material for MkDocs, pinned to `mkdocs<2`. Material stopped feature development in November 2025 and gets only critical fixes through 2027-05-05. We chose it anyway because it is exactly the stack docs.datarobot.com runs on (its pages report `mkdocs-1.6.1, mkdocs-material-9.6.15+insiders`). It is also mature, and `mkdocs build --strict` and mkdocstrings work today.

## Considered Options

- **Zensical**, Material's successor. It supports mkdocstrings but is a 0.x release, and its strict-build story is unverified. Migrating to it is the natural next step, not the starting point.
- **MkDocs 2.0**. Still pre-release, has no plugin system and is incompatible with Material.
- **Docusaurus**. It would show MDX/JS, but it loses the docstring-to-API-page flow that the drift story depends on.
