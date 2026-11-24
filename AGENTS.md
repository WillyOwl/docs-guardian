# AGENTS.md

## Git conventions

- Do not add co-author or AI attribution lines (e.g. `Co-Authored-By:`, "Generated with ...") to commits, PR descriptions, issue/PR comments, or anything else pushed to the remote repository.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on `WillyOwl/doc-guardian` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` plus `docs/adr/`. See `docs/agents/domain.md`.
