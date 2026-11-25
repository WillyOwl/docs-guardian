# Reproduce review round 5

Reviewed commit: `77120b704a46df07b8fa18c418863523e26e9cd6`.
Evidence directory: `77120b7/round-5/` on `pr11-review-evidence`.

1. Create a detached worktree at the reviewed commit. Keep the evidence directory outside its source tree.
2. Prepare Python 3.11 and 3.14 environments with the project's dev dependencies. For Notebook execution and a strict build, include the docs dependency group.
3. Set `PYTHONPATH` to `<reviewed-worktree>/src:<reviewed-worktree>/tinyml/src` and `PYTHONDONTWRITEBYTECODE=1`.
4. From the reviewed worktree, run `python -m pytest -p no:cacheprovider --color=no` under both interpreters. Expect 103 passed each.
5. Under both interpreters, run `python -m pytest <evidence-dir>/test_review_round5.py -vv --tb=short -p no:cacheprovider --color=no`. Expect 4 failures and 3 passes. The failures are independent expected-behavior assertions that reproduce the two findings, not pre-existing suite failures. Each fixture creates its own temporary Git repository; the PR worktree is never modified.
6. Run `python -m ruff check .` and `python -m ruff format --check .`.
7. Run `python -c 'from docs_guardian.cli import main; raise SystemExit(main())' snippets tinyml/docs` and the equivalent `drift --base origin/main --source tinyml/src --docs tinyml/docs`.
8. With docs dependencies, run `python -m pytest --nbmake tinyml/docs/notebooks -p no:cacheprovider --color=no` and `python -m mkdocs build --strict -f tinyml/mkdocs.yml -d <temporary-site-dir>`. Notebook execution needs permission to open local sockets.
9. Read the remote checks with `gh pr checks 11 --repo WillyOwl/docs-guardian`, and confirm the reviewed head with `gh pr view 11 --repo WillyOwl/docs-guardian --json headRefOid,state,isDraft`.
10. Run `git status --porcelain` and `git diff --check` to verify the reviewed worktree.

`capture.py` contains every exact command and environment used here, with local interpreter paths. Adapt those paths when running elsewhere. `render_screenshots.py` opens HTML containing escaped, complete saved command output in Chromium, captures each viewer, and records image/log hashes in `screenshots.json`.

| Output | Screenshot | Purpose |
| --- | --- | --- |
| [pytest-3.11.txt](pytest-3.11.txt) | [pytest-3.11.png](pytest-3.11.png) | Full existing suite |
| [pytest-3.14.txt](pytest-3.14.txt) | [pytest-3.14.png](pytest-3.14.png) | Full existing suite |
| [review-probes-3.11.txt](review-probes-3.11.txt) | [review-probes-3.11.png](review-probes-3.11.png) | F1/F2 reproductions and controls |
| [review-probes.txt](review-probes.txt) | [review-probes.png](review-probes.png) | F1/F2 reproductions and controls |
| [ruff.txt](ruff.txt) | [ruff.png](ruff.png) | Lint and format |
| [snippets.txt](snippets.txt) | [snippets.png](snippets.png) | Documentation Snippets |
| [notebooks.txt](notebooks.txt) | [notebooks.png](notebooks.png) | Authorized successful notebook run |
| [notebooks-sandbox.txt](notebooks-sandbox.txt) | [notebooks-sandbox.png](notebooks-sandbox.png) | Initial sandbox socket restriction |
| [build-docs.txt](build-docs.txt) | [build-docs.png](build-docs.png) | Strict docs build |
| [drift-current.txt](drift-current.txt) | [drift-current.png](drift-current.png) | Current PR's Drift Report |
| [ci.txt](ci.txt) | [ci.png](ci.png) | Remote checks and head SHA |
| [environment.txt](environment.txt) | [environment.png](environment.png) | Interpreter versions, imports, clean worktree |
