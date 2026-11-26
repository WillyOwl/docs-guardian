Standards review: no actionable findings.

Reviewed `d48615c3386b813d0fc6845a23e1588e3c57bf67...e7db35cdf9cd8c70e63dc592d821f9243875dc76` against AGENTS.md, GLOSSARY.md, ADRs 0001–0003, pyproject.toml conventions, README.md, and docs/architecture.md.

- **Documented-standard breaches:** none. README covers the new behavior, commands, and configuration. Domain vocabulary and separation between docs-guardian and the Guarded Project remain consistent.
- **Heuristic smells:** none warrant a change. Independent workflow jobs repeat a small setup sequence, consistent with existing workflows; extracting it would introduce unnecessary abstraction.

Evidence publication and remote review comments were excluded as requested.
