# PR #11 code review — round 3

Reviewed commit: `1c1ae382b858fb9c3aa9d8303a590df02773a34c`.
Base: `6af3ec1c790f170e064659a1f23ae2e1f6008c04` (`origin/main`).

**Result: no new actionable correctness findings in this review.** The five
round-2 findings are fixed and pass independent reproduction checks on the
current head. No implementation changes were made during this round.

## Scope

Read all eight changed files, the surrounding CLI and Snippet implementation,
GLOSSARY.md, ADRs 0001–0003, architecture documentation, tests, and both previous
review rounds. Examined public API extraction, signature comparison, code-only
Mentions, Markdown and notebook locations, Advisory error handling, merge-base
reading, comment identity and update behavior, report truncation, workflow
permissions, and README consistency.

## Previous findings and verdicts

| Point | Verdict | Verification at the reviewed commit |
| --- | --- | --- |
| R2 F1: union annotations could erase signature changes | fixed in `25cf3af` | Whole signatures remain structured; changing both parameter and return unions produces an API Change. Independent CLI probe passes. |
| R2 F2: pipes and backticks could break Markdown table cells | fixed in `25cf3af` | Independent table probes pass. A fresh CLI report containing a union, a backtick default and a Page named `quick\|start.md` was sent to GitHub's actual Markdown renderer; all three columns and both affected Pages survive. |
| R2 F3: valid JSON with malformed notebook structure could crash | fixed in `25cf3af` | The `cells: null` CLI reproduction returns 0 and lists the notebook as unreadable; the existing malformed-structure cases pass. |
| R2 F4: comment lookup failure could fail the Advisory workflow | fixed in `4df812c` | Independent stubbed HTTP 503 lookup returns 0 with a workflow warning. Initial POST, PATCH, clearing a report and forbidden POST also pass with the real script. |
| R2 F5: inline code could be located on preceding prose | fixed in `25cf3af` | The original two-line reproduction points to `guide.md:2`; existing list, blockquote and multiline-code cases pass. |
| Folder named like a Page or module could crash | fixed in `25cf3af` | Existing regression passes as part of both 99-test runs. |
| Many matching comments could cause SIGPIPE | fixed in `4df812c` | Existing 100,000-ID posting-script regression passes in both test runs. |

No new finding requires a fixed/declined verdict. Accepted limits already
documented in the PR (dataclass/inherited constructors and re-exports from
private modules) remain visible; this review does not reopen those decisions.

## Evidence

Every output below has a new Chromium screenshot with the same stem. See
[verification.md](verification.md) for reproduction steps and the full index.

| Check | Observed result | Complete output |
| --- | --- | --- |
| Full existing suite, Python 3.14.6 | 99 passed | [pytest-3.14.txt](pytest-3.14.txt) |
| Full existing suite, Python 3.11.15 | 99 passed | [pytest-3.11.txt](pytest-3.11.txt) |
| Independent review probes | 17 passed | [review-probes.txt](review-probes.txt) |
| Ruff lint and format | Both pass; 26 files already formatted | [ruff.txt](ruff.txt) |
| Snippet runner | 4 Pages passed | [snippets.txt](snippets.txt) |
| Notebook execution | 1 passed outside the sandbox | [notebooks.txt](notebooks.txt) |
| Strict documentation build | Exit 0 | [build-docs.txt](build-docs.txt) |
| Current PR's Drift Report | No API Changes, exit 0 | [drift-current.txt](drift-current.txt) |
| Isolated CLI report fixture | 3 API Changes, Drift on 2 Pages, added API undocumented | [report-demo.txt](report-demo.txt) |
| Real GitHub Markdown renderer | Two body rows, three cells per row; locations preserved | [github-render.txt](github-render.txt), [rendered screenshot](report-demo-rendered.png) |
| GitHub CI at the same head | All six checks pass | [ci.txt](ci.txt) |
| Environment and checkout provenance | Exact imports and versions recorded; reviewed checkout clean | [environment.txt](environment.txt) |

The 17 independent probes include the five original round-2 reproductions,
five additional mocked comment paths, and seven checks for nested Page/cell
locations, unreadable content, configuration errors, private modules, escaped
table content, and an oversized report with multibyte text. They are review
artifacts, stored only on the evidence branch.

## Limits

- A live bot's first Drift Report POST and subsequent PATCH remain unverified.
  Current CI takes the no-API-change path; posting tests use a stub `gh`, and
  the GitHub Markdown endpoint validates rendering rather than bot permissions.
- The first local notebook attempt could not create Jupyter sockets under the
  sandbox. Its complete failing output and screenshot are retained as
  `notebooks-sandbox.*`; an authorized rerun of the identical test passed.
- Existing environments were reused. PYTHONPATH explicitly selected the
  detached checkout's tooling and tinyml sources; imports and dependency
  versions are recorded. These are not claims of fresh environment installs.
- The strict build emitted the already documented Material end-of-life notice
  and exited 0. Its generated cache was moved outside the checkout.

README updated by the PR's implementation; no README change was necessary for
this review. The PR remains open and draft.
