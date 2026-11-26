# Standards review — round 2

Reviewed `eab5b3ca743838c270066d5c3f72f9a13582832a` with `git diff d48615c3386b813d0fc6845a23e1588e3c57bf67...HEAD`.

## Documented standards

No violations found in the diff. Reviewed AGENTS.md, GLOSSARY.md, docs/agents/domain.md, ADRs 0001–0003, README.md, docs/architecture.md and pyproject.toml. The README covers the new commands and layout, domain vocabulary is consistent, and the Gate does not change the drift check's Advisory behavior. Tool-enforced formatting and lint rules are excluded from this assessment. Remote evidence and PR administration are outside this read-only review.

## Judgment calls

1. **Possible Shotgun Surgery (low priority)** — `.github/scripts/check-links.sh:8` and `tests/test_check_links.py:48` copy the deployment URL already owned by `tinyml/mkdocs.yml:3`:

   ```bash
   site_url="https://willyowl.github.io/docs-guardian/" # site_url in tinyml/mkdocs.yml
   ```

   ```python
   SITE_URL = "https://willyowl.github.io/docs-guardian/"
   ```

   A deployment URL change requires coordinated edits in all three places. If only MkDocs changes, these tests still exercise the old URL and can pass while the actual site's URLs stop being remapped locally. Consider one configuration source, or a consistency check against MkDocs' `site_url`. This is a baseline heuristic, not a documented-standard violation; the repository's CI integrations already intentionally select tinyml.

Totals: 0 documented-standard violations; 1 low-priority baseline smell.
