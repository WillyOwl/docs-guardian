# The e2e tests open real Demo PRs on the real repo

docs-guardian's end-to-end suite (`tests/e2e/`) opens real draft pull requests on `WillyOwl/docs-guardian`. Each one is a Demo PR that breaks tinyml on purpose. The suite waits for the real workflows, asserts every check's result, the key log lines and the Drift Report comment, then closes the PR unmerged and deletes its branch. The project's promise is about pull requests: a Gate turns one red, and the drift check posts one comment and rewrites it on every push. Only a real pull request exercises the workflow files, the event triggers, the token's permissions and the comment posting together. The cost is that every run leaves closed PRs in the repo's history (GitHub cannot delete them), takes minutes, and needs a `gh` login that can push. So the suite is opt-in (`pytest -m e2e`), run by hand, and never part of CI.

## Considered Options

- **Breakage scenarios in a temporary local repo**: copy tinyml, break it, and run each check's command as its workflow does. This is fast, free and leaves no trace, but it re-implements the workflows in test code, so a broken workflow file, a missing permission or a comment-posting bug would pass.
- **Run the installed `docs-guardian` executable on fixtures**: this covers packaging and the entry point and little else; the in-process CLI tests already cover the rest.
- **Run the suite from a workflow** (on a schedule or by hand): pull requests and pushes made with a workflow's `GITHUB_TOKEN` do not trigger other workflows, so it would need a personal access token or a GitHub App as a secret. It can be added later on top of the same code.
