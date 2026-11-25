# How docs-guardian works

A visual walkthrough of the design. Terms in **bold** are defined in [`GLOSSARY.md`](../GLOSSARY.md); the reasoning behind the shape is in [`docs/adr/`](./adr/).

## 1. The big picture

docs-guardian watches a **Guarded Project** (tinyml: its source code and its **Pages**) and answers one question from several angles: *do the docs still match the code?* Two of its checks are **Gates** that can turn a pull request red; the other two are **Advisory** and only publish a report.

```mermaid
flowchart LR
    subgraph GP["Guarded Project · tinyml/"]
        SRC["Source code<br/>tinyml/src"]
        PAGES["Pages<br/>tinyml/docs<br/>Markdown + one notebook"]
    end

    subgraph DG["docs-guardian"]
        subgraph GATES["Gates · can fail a PR"]
            SN["Snippet runner"]
            LINT["Lint · links · strict build"]
        end
        subgraph ADV["Advisory · only report"]
            DR["Drift check"]
            HB["Health bot"]
        end
    end

    PAGES --> SN
    SRC -. "imported by Snippets" .-> SN
    PAGES --> LINT
    SRC --> DR
    PAGES --> DR
    SRC --> HB
    PAGES --> HB

    SN --> CHECK["PR check<br/>red / green"]
    LINT --> CHECK
    DR --> DREP["Drift Report<br/>one PR comment"]
    HB --> HREP["Health Report<br/>one GitHub issue"]
```

Each check catches a different kind of rot:

| Check | Kind | Catches | Can't catch |
| --- | --- | --- | --- |
| Snippet runner | Gate | Snippets and notebooks that no longer run | Code that runs but is described wrongly |
| Lint · links · strict build | Gate | Bad formatting, house-style violations, broken links, broken nav | Anything about meaning |
| Drift check | Advisory | Pages that Mention an API a PR removed or changed | Prose that names an API without code formatting |
| Health bot | Advisory | Explanations that no longer match behaviour; Pages contradicting each other | Nothing deterministic: it can miss and it can be wrong |

## 2. When each check runs

Fast, free checks run on every pull request. Anything slow or paid runs after merge, on a schedule, or by hand.

```mermaid
flowchart LR
    PR(["Pull request<br/>opened or pushed"]) --> SN["Snippet runner<br/>+ notebooks via nbmake"]
    PR --> LINT["Lint · links · strict build"]
    PR --> DR["Drift check"]

    MAIN(["Push to main"]) --> DEPLOY["Build + deploy site<br/>to GitHub Pages"]

    CRON(["Weekly schedule<br/>or manual run"]) --> HB["Health bot"]

    YOU(["You run<br/>docs-guardian eval"]) --> EVAL["Health bot × 3<br/>on the Planted Error fixture"]

    SN --> R1["red / green"]
    LINT --> R1
    DR --> R2["Drift Report"]
    HB --> R3["Health Report"]
    EVAL --> R4["found / missed / false positives<br/>→ numbers in README"]
```

Next, if time allows (cut from the three-day scope): release notes from merged PRs, and an `llms.txt` index for AI assistants.

## 3. Inside each check

### Snippet runner (Gate)

Every Markdown Page runs on its own, in a fresh process group and an empty folder, so one Page can never make another pass or hang the whole run, and a Page passes only if it works from a reader's blank folder.

```mermaid
flowchart TD
    A["A Markdown Page"] --> B["Pull out its Snippets in order<br/>leave out Skipped Snippets"]
    B --> C["Run them in a fresh subprocess, in an empty folder<br/>one shared namespace · timeout"]
    C -->|every Snippet ran| P["Page passed"]
    C -->|a Snippet raised| F["Page failed<br/>exact line in the Page + the error<br/>+ how many Snippets did not run"]
    C -->|timeout| F
    C -->|process died| F
    F --> X["exit 1 → PR check red"]
    NB["Notebook Pages"] --> NBM["nbmake via pytest"] -->|a cell failed| X
```

When the Page ends, by finishing, failing or timing out, every process it started is killed with it. Snippet output is discarded. Snippets are found by parsing the Page as CommonMark, the way a renderer does: fences inside lists and blockquotes count, fences inside HTML comments don't. A Snippet is skipped with `<!-- docs-guardian: skip -->` on the line above its fence. Run it with `docs-guardian snippets <docs-root>`; it exits 1 if any Page fails, and 2 if the folder holds no Pages, so a mistyped path cannot pass.

### Drift check (Advisory)

It compares the public API before and after the pull request, then finds where the Pages use anything that changed. The PR check stays green (ADR 0001).

```mermaid
flowchart TD
    BASE["Source at the PR's merge base"] --> APIB["Public API before<br/>public name → signature"]
    HEAD["Source at the PR head"] --> APIH["Public API after"]
    APIB --> CMP["Compare by public name<br/>(moving code between modules is not a change)"]
    APIH --> CMP
    CMP --> CH["API Changes<br/>added · removed · changed"]
    CH -->|removed or changed| M["Find Mentions in Pages' code<br/>Snippets · inline code · notebook cells"]
    M --> D["Drift<br/>Page + line for each API Change"]
    CH -->|added, never Mentioned| U["Not yet documented"]
    D --> REP["Drift Report<br/>one PR comment, rewritten on every push"]
    U --> REP
```

A signature is the parameters, their defaults and annotations, and the return annotation; a name defined more than once keeps all its signatures. A class's signature is its own `__init__`. Known gaps: a class whose constructor comes from elsewhere (a dataclass, an inherited `__init__`) shows as `()`, and API defined in a private module (`_impl.py`) and re-exported is not seen. A top-level name is Mentioned on its own or after its package path (`tinyml.fit`), never as another object's attribute (`model.fit`).

Run it with `docs-guardian drift --base <branch> --source <dir> --docs <dir>`. It exits 0 whatever it finds; files the pull request leaves unreadable are listed in the report, not fatal; a mistyped base or folder exits 2. The workflow posts the report as one comment and rewrites it on every push (one run per pull request at a time); with no API Changes and no earlier report it posts nothing, and when GitHub's API fails (a fork's read-only token, an outage) it warns and the report stays in the job summary. The posting lives in `.github/scripts/post-drift-report.sh`, so its tests run the real script against a stub `gh`.

### Health bot (Advisory)

The language model reads the whole site at once, so it can also spot two Pages that disagree. Every claim it makes must point at real text, or it is thrown away.

```mermaid
flowchart TD
    P["All Pages"] --> LLM["One Claude call<br/>structured output"]
    API["Public API + docstrings<br/>the source of truth"] --> LLM
    LLM --> C["Candidate Findings<br/>Page · Quote · Problem · Severity<br/>Suggested Fix · Conflicting Quote?"]
    C --> V{"Is every Quote really<br/>in its Page?"}
    V -->|no| DROP["dropped"]
    V -->|yes| F["Findings"]
    F --> ANY{"Any Findings?"}
    ANY -->|yes| OPEN["Health Report open or reopened<br/>body replaced with the latest Findings"]
    ANY -->|no| CLOSE["Health Report closed<br/>No Findings as of date"]
```

Severity is **Wrong** (following the Page gives an error or a wrong result) or **Misleading** (the code works, the explanation doesn't match).

To measure the bot, `docs-guardian eval` runs it three times on a test Page holding five **Planted Errors** whose Quotes are known. It counts how many it found, how many it missed, and how many other things it flagged (false positives).

### Lint · links · strict build (Gate)

Mostly configuration; each runs as its own PR check.

| Tool | Catches |
| --- | --- |
| markdownlint-cli2 | Inconsistent headings, lists, whitespace |
| Vale + a `DocsGuardian` style | House-style violations, e.g. "Github" instead of "GitHub" |
| lychee | Broken internal and external links |
| `mkdocs build --strict` | Broken cross-references, Pages missing from the nav |

## 4. One change, every check

Say a pull request renames `fit_linear` to `fit` and doesn't touch the docs:

| Check | What you see |
| --- | --- |
| Snippet runner | Red: `quickstart.md:14  NameError: name 'fit_linear' is not defined`, plus how many Snippets did not run |
| Drift check | Drift Report: `fit_linear` removed, Mentioned in `quickstart.md:14` and `tutorial.md:31`; `fit` not yet documented |
| Lint · links · strict build | Green: the API pages are generated from docstrings, so nothing in the nav breaks |
| Health bot | Nothing yet. It runs on the next schedule, after merge, and the Gate stops this PR merging first |

## 5. Where things live

```text
docs-guardian/                  ← the repo
├── src/docs_guardian/          ← the tooling, one CLI: snippets · drift · health · eval
├── tests/
│   └── fixtures/planted/       ← the Planted Error test Page + expected Quotes
├── tinyml/                     ← the Guarded Project, self-contained
│   ├── src/tinyml/
│   ├── docs/                   ← its Pages (published to GitHub Pages)
│   └── mkdocs.yml
├── docs/                       ← docs-guardian's own docs (never published, never scanned)
│   ├── architecture.md         ← this page
│   └── adr/
├── .github/workflows/          ← one workflow per trigger
├── .github/scripts/            ← the drift check's comment poster
└── GLOSSARY.md
```
