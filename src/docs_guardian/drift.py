"""The drift check: find API Changes in a pull request and the Pages that Mention them."""

import ast
import json
import re
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

from markdown_it import MarkdownIt

from docs_guardian.snippets import extract_snippets

_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
_MARKDOWN = MarkdownIt("commonmark")

REPORT_MARKER = "<!-- docs-guardian:drift-report"
"""Opens the hidden first line of every Drift Report, so a later push finds and rewrites it."""

SIGNATURE_SEPARATOR = " | "
"""Joins the signatures of a name defined more than once (overloads, or two modules)."""


class DriftConfigError(Exception):
    """The drift check was pointed at something that isn't there: a bad base or path."""


# --- Public API -----------------------------------------------------------------


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Parameters, their defaults and annotations, and the return annotation."""
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"({ast.unparse(node.args)}){returns}"


def _add(api: dict[str, str], name: str, signature: str) -> None:
    """Record a signature, keeping every distinct one for a name defined more than once."""
    known = set(api[name].split(SIGNATURE_SEPARATOR)) if name in api else set()
    api[name] = SIGNATURE_SEPARATOR.join(sorted(known | {signature}))


def public_api(source: str) -> dict[str, str]:
    """Collect the public API one module defines.

    Public means defined at the module's top level with a name that has no
    leading underscore: functions, and classes with their non-underscore
    methods. A class's own signature is its `__init__`, or `()` if it defines
    none (an inherited `__init__` or a dataclass's generated one is a known
    gap). Docstrings and decorators are not part of a signature. A name defined
    more than once keeps all its signatures, so a change to any one shows.

    Args:
        source: The module's Python source.

    Returns:
        Public name (`fit_linear`, `LinearModel`, `LinearModel.predict`) to
        signature (`(X, y) -> LinearModel`).

    Raises:
        SyntaxError: If the source does not parse.
    """
    api: dict[str, str] = {}
    for node in ast.parse(source).body:
        name = getattr(node, "name", None)
        if name is None or name.startswith("_"):
            continue
        if isinstance(node, _FUNCTIONS):
            _add(api, name, _signature(node))
        elif isinstance(node, ast.ClassDef):
            methods = [item for item in node.body if isinstance(item, _FUNCTIONS)]
            init = next((m for m in methods if m.name == "__init__"), None)
            _add(api, name, _signature(init) if init else "()")
            for method in methods:
                if not method.name.startswith("_"):
                    _add(api, f"{name}.{method.name}", _signature(method))
    return api


def _is_private(path: str) -> bool:
    """A module or package whose name starts with `_` (other than `__init__.py`)."""
    return any(p.startswith("_") and p != "__init__.py" for p in PurePosixPath(path).parts)


def package_api(files: dict[str, str]) -> dict[str, str]:
    """Collect the public API of a package, keyed by public name.

    Modules and packages whose name starts with an underscore are private and
    skipped (`__init__.py` is public), so API defined in a private module and
    re-exported is a known gap. Keying by name, not by module, means moving a
    function between modules is not an API Change.

    Args:
        files: Path (relative to the source root, `/`-separated) to Python source.

    Returns:
        Public name to signature, across every public module.

    Raises:
        SyntaxError: If a public module does not parse.
    """
    api: dict[str, str] = {}
    for path, source in sorted(files.items()):
        if not _is_private(path):
            for name, signature in public_api(source).items():
                for one in signature.split(SIGNATURE_SEPARATOR):
                    _add(api, name, one)
    return api


# --- API Changes ----------------------------------------------------------------


class ChangeKind(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True)
class ApiChange:
    """A public function, class or method added, removed, or given a new signature.

    Attributes:
        name: Its public name, e.g. `fit_linear` or `LinearModel.predict`.
        kind: Added, removed or changed.
        old: The signature before, or None if added.
        new: The signature after, or None if removed.
    """

    name: str
    kind: ChangeKind
    old: str | None
    new: str | None


def api_changes(before: dict[str, str], after: dict[str, str]) -> list[ApiChange]:
    """Find the API Changes between two public APIs.

    Args:
        before: Public name to signature at the pull request's merge base.
        after: The same for the checkout being reviewed.

    Returns:
        The API Changes, ordered by name.
    """
    changes = []
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        if old is None:
            kind = ChangeKind.ADDED
        elif new is None:
            kind = ChangeKind.REMOVED
        else:
            kind = ChangeKind.CHANGED
        changes.append(ApiChange(name, kind, old, new))
    return changes


# --- Mentions -------------------------------------------------------------------


@dataclass(frozen=True)
class Mention:
    """One place a Page's code uses a public name.

    Attributes:
        page: The Page, relative to the docs root, `/`-separated.
        line: Line in the Page, or in the notebook cell.
        cell: Notebook cell number, or None for a Markdown Page.
    """

    page: str
    line: int
    cell: int | None = None

    @property
    def where(self) -> str:
        """Readable location: `quickstart.md:8` or `walk.ipynb (cell 2, line 1)`."""
        if self.cell is None:
            return f"{self.page}:{self.line}"
        return f"{self.page} (cell {self.cell}, line {self.line})"

    @property
    def order(self) -> tuple[str, int, int]:
        """Sort key: Page path, then cell, then line."""
        return (self.page, self.cell or 0, self.line)


def _pattern(name: str, packages: Iterable[str]) -> re.Pattern[str]:
    """How a name appears in code.

    A method (`LinearModel.predict`) is any `.predict` attribute. A top-level
    name counts on its own or after its package path (`tinyml.fit`), never as
    another object's attribute (`model.fit`).
    """
    if "." in name:
        return re.compile(rf"\.{re.escape(name.rsplit('.', 1)[1])}\b")
    paths = "|".join(rf"\b{re.escape(p)}(?:\.\w+)*\." for p in packages)
    via_package = rf"(?:{paths}){re.escape(name)}\b" if paths else None
    bare = rf"(?<![\w.]){re.escape(name)}\b"
    return re.compile(f"{via_package}|{bare}" if via_package else bare)


def _markdown_code(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line, code) for every line of a Snippet and every inline code span."""
    for snippet in extract_snippets(text):  # Skipped Snippets are still shown to readers
        for offset, line in enumerate(snippet.code.splitlines()):
            yield snippet.line + offset, line
    for token in _MARKDOWN.parse(text):
        if token.type != "inline" or token.map is None:
            continue
        cursor = 0
        for child in token.children or []:
            if child.type != "code_inline":
                continue
            at = token.content.find(child.content, cursor)
            if at < 0:  # whitespace was normalised; fall back to where the last span ended
                at = cursor
            cursor = at + len(child.content)
            yield token.map[0] + 1 + token.content[:at].count("\n"), child.content


def _notebook_code(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield (cell number, line number, code) for every line of every code cell."""
    for number, cell in enumerate(json.loads(text).get("cells", []), 1):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else source
        for line_number, line in enumerate(source.splitlines(), 1):
            yield number, line_number, line


def _pages(docs_root: Path) -> list[Path]:
    return sorted(p for p in docs_root.rglob("*") if p.suffix in {".md", ".ipynb"})


def find_mentions(
    docs_root: Path,
    names: Iterable[str],
    packages: Iterable[str] = (),
    unreadable: list[str] | None = None,
) -> dict[str, list[Mention]]:
    """Find where each public name is used in the Pages' code.

    Only code counts: Snippets (skipped ones too), inline code spans, and
    notebook code cells. Prose that names an API is not a Mention.

    Args:
        docs_root: Folder searched recursively for `*.md` and `*.ipynb` Pages.
        names: Public names, e.g. `fit_linear` or `LinearModel.predict`.
        packages: Top-level package names, so `tinyml.fit` counts as `fit`.
        unreadable: If given, Pages that could not be read (not UTF-8, or a
            notebook that isn't JSON) are appended here instead of raising.

    Returns:
        Each name mapped to its Mentions, in Page order; empty if none.
    """
    root = Path(docs_root)
    packages = list(packages)
    patterns = {name: _pattern(name, packages) for name in names}
    found: dict[str, list[Mention]] = {name: [] for name in patterns}
    for page in _pages(root):
        relative = page.relative_to(root).as_posix()
        try:
            text = page.read_text(encoding="utf-8")
            if page.suffix == ".md":
                places = [(Mention(relative, line), code) for line, code in _markdown_code(text)]
            else:
                places = [
                    (Mention(relative, line, cell), code)
                    for cell, line, code in _notebook_code(text)
                ]
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            if unreadable is None:
                raise
            unreadable.append(relative)
            continue
        for name, pattern in patterns.items():
            hits = {mention for mention, code in places if pattern.search(code)}
            found[name] += sorted(hits, key=lambda m: m.order)
    return found


# --- The Drift Report -------------------------------------------------------------


def _git(*args: str, cwd: Path) -> str:
    """Run git and return its stdout, raising CalledProcessError on failure."""
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _read_api(files: dict[str, str], unreadable: list[str]) -> dict[str, str]:
    """`package_api`, skipping public modules that do not parse (noted in `unreadable`)."""
    readable = {}
    for path, source in files.items():
        try:
            if not _is_private(path):
                public_api(source)
            readable[path] = source
        except SyntaxError:
            unreadable.append(path)
    return package_api(readable)


def _source_at_merge_base(base: str, source_root: Path) -> tuple[str, dict[str, str]]:
    """The merge base of `base` and HEAD, and the Python files under `source_root` there."""
    try:
        top = Path(_git("rev-parse", "--show-toplevel", cwd=source_root).strip())
        merge_base = _git("merge-base", base, "HEAD", cwd=top).strip()
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip().splitlines()[-1] if error.stderr.strip() else ""
        raise DriftConfigError(
            f"cannot find the merge base of {base} and HEAD: {detail}"
        ) from error
    prefix = source_root.resolve().relative_to(top.resolve()).as_posix()
    listed = _git("ls-tree", "-r", "--name-only", "-z", merge_base, "--", prefix, cwd=top)
    files = {}
    for path in listed.split("\0"):
        if path.endswith(".py"):
            raw = subprocess.run(
                ["git", "show", f"{merge_base}:{path}"], cwd=top, check=True, capture_output=True
            ).stdout
            files[PurePosixPath(path).relative_to(prefix).as_posix()] = raw.decode(
                "utf-8", "replace"
            )
    return merge_base, files


def _source_in_checkout(source_root: Path) -> dict[str, str]:
    """The Python files under `source_root` as they are on disk, uncommitted edits included."""
    return {
        path.relative_to(source_root).as_posix(): path.read_text(encoding="utf-8", errors="replace")
        for path in source_root.rglob("*.py")
    }


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def render_report(
    changes: list[ApiChange],
    mentions: dict[str, list[Mention]],
    base: str,
    merge_base: str,
    unreadable: Iterable[str] = (),
) -> str:
    """Render the Drift Report: one Markdown comment for the pull request.

    Args:
        changes: The API Changes.
        mentions: Each changed name's Mentions.
        base: The branch compared against, e.g. `main`.
        merge_base: The commit compared against.
        unreadable: Files skipped because they could not be read or parsed.

    Returns:
        The report, opening with a hidden marker that carries the counts.
    """
    gone = [c for c in changes if c.kind is not ChangeKind.ADDED]
    drift_pages = {m.page for c in gone for m in mentions.get(c.name, [])}
    undocumented = [
        c.name for c in changes if c.kind is ChangeKind.ADDED and not mentions.get(c.name)
    ]
    lines = [
        f"{REPORT_MARKER} changes={len(changes)} drift-pages={len(drift_pages)} -->",
        "### Drift Report",
        "",
        f"Public API in this checkout, compared with its merge base with `{base}` "
        f"(`{merge_base[:7]}`). Advisory: this check never fails the build.",
        "",
    ]
    if not changes:
        lines.append("No API Changes.")
    else:
        drift = f"Drift on {_plural(len(drift_pages), 'Page')}" if drift_pages else "no Drift"
        lines.append(f"{_plural(len(changes), 'API Change')}; {drift}.")
    if gone:
        lines += ["", "| API | Change | Pages that Mention it |", "| --- | --- | --- |"]
        for change in gone:
            if change.kind is ChangeKind.REMOVED:
                what = "removed"
            else:
                what = f"`{change.old}` → `{change.new}`"
            where = ", ".join(f"`{m.where}`" for m in mentions.get(change.name, [])) or "none"
            lines.append(f"| `{change.name}` | {what} | {where} |")
    if undocumented:
        names = ", ".join(f"`{name}`" for name in undocumented)
        lines += ["", f"**Not yet documented**: no Page Mentions {names}."]
    if unreadable:
        files = ", ".join(f"`{path}`" for path in sorted(set(unreadable)))
        lines += ["", f"**Could not read** (skipped; not valid Python, UTF-8 or JSON): {files}."]
    return "\n".join(lines) + "\n"


def drift_report(base: str, source_root: Path, docs_root: Path) -> str:
    """Build the Drift Report for the current checkout.

    Files the pull request leaves unreadable (a syntax error, a Page that isn't
    UTF-8, a notebook that isn't JSON) are skipped and listed in the report:
    the check is Advisory, so content problems never fail it.

    Args:
        base: The branch the pull request merges into, e.g. `origin/main`.
        source_root: Folder holding the Guarded Project's Python packages.
        docs_root: Folder holding its Pages.

    Returns:
        The rendered Drift Report.

    Raises:
        DriftConfigError: If the base has no merge base with HEAD, or either
            folder holds nothing to check (likely a mistyped path).
    """
    source_root, docs_root = Path(source_root), Path(docs_root)
    if not source_root.is_dir() or not any(source_root.rglob("*.py")):
        raise DriftConfigError(f"no Python files under {source_root}")
    if not docs_root.is_dir() or not _pages(docs_root):
        raise DriftConfigError(f"no Pages under {docs_root}")
    unreadable: list[str] = []
    merge_base, files_before = _source_at_merge_base(base, source_root)
    before = _read_api(files_before, [])  # the base's own problems are not this PR's
    after = _read_api(_source_in_checkout(source_root), unreadable)
    changes = api_changes(before, after)
    packages = [p.name for p in source_root.iterdir() if (p / "__init__.py").is_file()]
    mentions = find_mentions(docs_root, [c.name for c in changes], packages, unreadable)
    return render_report(changes, mentions, base, merge_base, unreadable)
