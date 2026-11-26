# PR #12 — independent review, round 1

Source head: `e7db35cdf9cd8c70e63dc592d821f9243875dc76`.
Base: `d48615c3386b813d0fc6845a23e1588e3c57bf67`.
Evidence branch: `pr12-review-evidence` (storage only).

Read [review.md](review.md) for the final findings and every independent report's disposition. The source branch was not modified. Two P2 coverage gaps remain open.

Each command capture has a `.txt` log, a `.png` screenshot, and the exact `.html` used to display the log in Chromium. The screenshots display real captured output; `notebook-rendered.png` separately shows the actual built mutation Page. Deliberately broken fixtures are marked as mutations, rather than presented as the pristine branch.

| Capture | Expected result / what it proves |
| --- | --- |
| `tool-versions` | Python 3.14.6, Markdownlint 0.24.0, Vale 3.26.0, lychee 0.24.2; reused release binary hashes |
| `markdownlint` | 4 Markdown Pages, 0 issues |
| `vale` | 4 Markdown Pages, 0 errors |
| `strict-build` | Clean strict build |
| `links` | Original online lychee invocation, 0 errors |
| `pytest` | 107 tests pass |
| `ruff` | Lint and formatting pass |
| `ci` | All 10 CI checks successful on the exact reviewed head |
| `notebook-anchor` | Offline deterministic notebook bad-anchor reproduction; harness exit 1 because both Gates incorrectly pass |
| `notebook-anchor-online` | Same bad anchor with the original online lychee invocation; harness exit 1 |
| `notebook-anchor-minimal` | Notebook reduced to a single Markdown cell; harness exit 1 |
| `anchor-controls` | Enable fragment checking: invalid anchor rejected; valid anchor passes. Put bad anchor in Markdown: strict build rejects it. Harness exit 0 |
| `same-site-url` | Offline deterministic same-site bad-page reproduction; harness exit 1 |
| `same-site-url-online` | Same bad-page URL with original online invocation; one extra link excluded, harness exit 1 |
| `same-site-controls` | Remap same public URL to local build: rejected. Equivalent relative bad URL: rejected. Harness exit 0 |
| `browser-dom` | Visible rendered notebook link exists but target ID does not; harness exit 0 |
| `source-integrity` | Correct reviewed head, no tracked or untracked source changes; whitespace check passes |

Review documents: [Standards raw report](standards-review.md), [Spec raw report](spec-review.md), [final review and dispositions](review.md).

Reproduction: [verification.md](verification.md). Scripts and minimized fixtures are under `tools/` and `fixtures/`. `manifest.json` records SHA-256 and size of every artifact except the manifest itself.
