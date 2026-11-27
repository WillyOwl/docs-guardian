# docs-guardian

docs-guardian is tooling that catches documentation that has fallen out of step with the code it describes, before readers do. It guards a separate Guarded Project; it is not the project itself.

## Language

### The two sides

**docs-guardian**:
The tooling: the checks and bots that inspect a Guarded Project's docs. Never the demo library or its site.
_Avoid_: doc-guardian, the library

**Guarded Project**:
The library plus docs site that docs-guardian protects; here, tinyml, kept deliberately small so it can be broken on purpose.
_Avoid_: the stage, the demo app, the library (unqualified)

### Kinds of check

**Gate**:
A docs-guardian check that can fail a pull request.
_Avoid_: blocker, required check (that is a GitHub setting, not the concept)

**Advisory**:
A docs-guardian check that only publishes a report and never fails anything.
_Avoid_: warning check, soft check, non-blocking

**Demo PR**:
A pull request that breaks the Guarded Project on purpose to show how docs-guardian's checks respond; never merged.
_Avoid_: test PR, fake PR, e2e PR

### Documentation units

**Page**:
One documentation file of the Guarded Project, either a Markdown file or a notebook.
_Avoid_: doc, file, article

**Snippet**:
One fenced `python` block inside a Markdown Page. Notebook cells are not Snippets.
_Avoid_: example, code block, block, cell

**Skipped Snippet**:
A Snippet explicitly marked as not to be run (pseudo-code, needs network).
_Avoid_: ignored block, disabled example

### What goes wrong

**API Change**:
A public function or method of the Guarded Project that was added, removed, or given a different signature between two versions.
_Avoid_: breaking change (an API Change need not break anything), diff

**Mention**:
A use of an API's public name inside a Page's code: a Snippet, an inline code span, or a notebook code cell. Prose that names an API is not a Mention.
_Avoid_: reference, occurrence

**Drift**:
A Page that Mentions an API that was removed or changed. Deterministic, computed per pull request.
_Avoid_: stale doc, outdated page

**Finding**:
A problem in a Page reported by the language model, always anchored to a Quote. Probabilistic, computed on a schedule.
_Avoid_: issue (collides with GitHub issues), error, warning

**Quote**:
The verbatim text from a Page that a Finding points at; a Finding whose Quote is not in the Page is discarded.
_Avoid_: excerpt, snippet (a Snippet is code)

**Conflicting Quote**:
A second Quote, from another Page, that a Finding says contradicts its Quote.
_Avoid_: counter-quote, related quote

**Severity**:
How a Finding hurts a reader. **Wrong**: following the Page gives an error or a wrong result. **Misleading**: the code works but the explanation no longer matches behaviour.
_Avoid_: high/medium/low, priority

**Planted Error**:
A deliberate mistake placed in a test Page, outside the Guarded Project's site, with its expected Quote recorded so Findings can be scored against it.
_Avoid_: seeded bug, test error, canary

### Reports

**Drift Report**:
The single comment on a pull request listing its API Changes and the Drift each one causes; revised in place on every push.
_Avoid_: drift comment, bot comment

**Health Report**:
The single GitHub issue holding the latest Findings across all Pages; revised in place on every run.
_Avoid_: health issue, audit, site report
