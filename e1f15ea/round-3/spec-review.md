## Spec

1. **[P2] Reject relative links that escape the published site** — `.github/scripts/check-links.sh:20–23`.

   Spec: “lychee | Broken internal and external links” (`spec-source.md:150`).

   `--root-dir` constrains root-relative URLs, but ordinary relative links still resolve against the build’s real filesystem location. A notebook link `[Repository readme](../../../../README.md)` renders unchanged at `site/notebooks/walkthrough/index.html`; lychee finds the repository’s unpublished `README.md` and passes. On the deployed project site, the same URL resolves to `/README.md`, outside `/docs-guardian/`. Thus a broken published link can leave both `strict-build` and `links` green. Resolve relative URLs within a simulated HTTP publication root, or reject targets that escape the published build; add a notebook regression case.

   Independently reproduced with a copied tinyml project: strict build exited 0 and the real link script exited 0 when only HTTP checking was disabled. A smaller entirely local fixture (`site/nested/index.html` → `../../outside.html`, where `outside.html` exists beside `site/`) also passed the unmodified script.

No additional missing requirements or unrequested scope found. Existing five link-check tests passed; a fresh 404-only broken-link probe failed as expected. Removing the notebook from nav and adding a missing Markdown cross-reference each failed the strict build as required.
