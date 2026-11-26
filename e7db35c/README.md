# Evidence at e7db35c

Every `.txt` file is a command's full output, with ANSI colour codes removed. Its first line is the command, run in a detached worktree of `e7db35c`:
- `wt`: the branch as it is;
- `wt-planted`: a scratch copy where one violation is planted per run, then reset.

Each `.png` is its `.txt` rendered by `tools/render.cjs` in headless Chromium. Scratchpad paths are shortened to `<scratchpad>`. Vale 3.26.0 and lychee 0.24.2 are the release binaries, checked against the SHA-256s that `docs-lint.yml` pins.

| File | What it shows |
| --- | --- |
| `markdownlint` / `-planted` | 0 issues in tinyml's Pages; an h3 straight after the h1 fails with MD001 at `quickstart.md:23` |
| `vale` / `-planted` | 0 errors; "Github" in `index.md` prose fails with `DocsGuardian.Terms` |
| `strict-build` / `-planted-nav` / `-planted-anchor` | The site builds strictly; a Page missing from the nav, and a link to a missing heading, each abort the build |
| `links` / `-planted` | 0 broken links in the built site; a dead external link and a dead link in a notebook Markdown cell both fail, while the strict build passes on that same copy |
| `pytest-3.14`, `pytest-3.11`, `ruff` | docs-guardian's own suite (107 passed) and lint, unchanged by this PR |
| `ci` | All ten PR checks pass on e7db35c, with the new jobs' checksum and result lines |
