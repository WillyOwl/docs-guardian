# AGENTS.md

## Git conventions

- Do not add co-author or AI attribution lines (e.g. `Co-Authored-By:`, "Generated with ...") to commits, PR descriptions, issue/PR comments, or anything else pushed to the remote repository.

-  Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `<type>(<optional scope>): <summary>`, with types such as `feat`, `fix`, `docs`, `test`, `ci`, `refactor`, `chore`. Mark breaking changes with `!` or a `BREAKING CHANGE:` footer.

## Branching

- Never commit to `main` directly, not even one-line docs fixes. Every change goes on its own branch and reaches `main` through a pull request.
- Name branches `<type>/<short-kebab-case-summary>`. `<type>` is the Conventional Commit type of the branch's main change (`feat`, `fix`, `docs`, `test`, `ci`, `refactor`, `chore`). The summary is 2–4 lowercase words naming what is being implemented, e.g. `feat/snippet-runner`, `fix/snippet-line-offset`, `docs/branching-rule`. No dates or usernames.
- Write the PR title as a Conventional Commit; it becomes the squash commit on `main`.
- Keep `README.md` current within the same PR. When the PR changes what the project does, how to install or set it up, how to run it (commands, options, configuration), how to run tests or build the docs, or the top-level repo layout, update `README.md` to match. The README stays a short entry point (what this is, quickstart, links into `docs/`); detail lives in `docs/`. State "README updated" or "README unaffected" in the PR body.
- Open pull requests; never merge them. The maintainer merges, by squash merge.
- After pushing new commits to a branch with an open PR, update the PR description and its evidence (test output, screenshots, verification steps) with `gh pr edit`. Screenshots are required: every test run or check cited as evidence has a fresh screenshot taken against the latest commit, with test output and verification steps alongside it. A PR whose diff touches only `README.md` is exempt from screenshots; its test output and verification steps are still required. The PR is up to date when every claim and every piece of evidence in its body, screenshots included, matches the branch's latest commit.
- Before starting new work, clean up:
  1. For each local branch other than `main`, check its PR with `gh pr list --head <branch> --state merged`.
  2. `git switch main && git pull --ff-only`.
  3. Force-delete (`git branch -D`) only the branches whose PR is confirmed **merged**. Squash merges make `git branch -d` refuse, so `-D` is expected, and the merged check is what makes it safe. Leave branches whose PR is open, closed unmerged, or missing.
  4. `git fetch --prune`, then branch the new work from the fresh `main`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on `WillyOwl/docs-guardian` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` plus `docs/adr/`. See `docs/agents/domain.md`.
