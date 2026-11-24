"""The snippet runner: run every Snippet of every Markdown Page, one Page per process."""

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 30.0
"""Seconds a Page may run before it fails with a Timeout."""

SKIP_MARKER = "<!-- docs-guardian: skip -->"
"""Put on the line directly above a fence to make that Snippet a Skipped Snippet."""

PYTHON_INFO_WORDS = frozenset({"python", "py", "python3"})
"""Info-string first words, case-insensitive, that make a fence a Snippet."""

# A fence opens with 3+ backticks or tildes, indented at most 3 spaces (CommonMark).
_OPENING_FENCE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class Snippet:
    """One fenced `python` block of a Page.

    Attributes:
        line: Line number in the Page of the Snippet's first code line.
        code: The Snippet's source, with the fence's indentation removed.
        skip: True for a Skipped Snippet: the line above its fence is the skip marker.
    """

    line: int
    code: str
    skip: bool = False


@dataclass(frozen=True)
class PageResult:
    """What happened when a Page's Snippets ran.

    Attributes:
        page: The Page.
        ran: Snippets that ran to completion.
        skipped: Skipped Snippets.
        not_run: Snippets after a failure, which never ran.
        line: Line in the Page where the failure happened, or None.
        error: The failure, e.g. "NameError: name 'x' is not defined", or None.
    """

    page: Path
    ran: int
    skipped: int
    not_run: int = 0
    line: int | None = None
    error: str | None = None

    @property
    def passed(self) -> bool:
        """True when every Snippet that was not skipped ran without raising."""
        return self.error is None


def extract_snippets(text: str) -> list[Snippet]:
    """Find the Snippets of a Markdown Page.

    Fences follow CommonMark: a fence closes only on a line of the same
    character, at least as long as the opening fence, with nothing else on it.
    A fence is a Snippet when its info string's first word is `python`, `py` or
    `python3`, in any case.

    Args:
        text: The Page's Markdown source.

    Returns:
        The Snippets in Page order, Skipped Snippets included.
    """
    snippets: list[Snippet] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        opening = _OPENING_FENCE.match(lines[i])
        if opening is None or (opening["fence"][0] == "`" and "`" in opening["info"]):
            i += 1
            continue
        fence, indent = opening["fence"], len(opening["indent"])
        closing = re.compile(rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")
        end = i + 1
        while end < len(lines) and not closing.match(lines[end]):
            end += 1
        words = opening["info"].split()
        if words and words[0].lower() in PYTHON_INFO_WORDS:
            body = [_dedent(line, indent) for line in lines[i + 1 : end]]
            skip = i > 0 and lines[i - 1].strip() == SKIP_MARKER
            snippets.append(Snippet(line=i + 2, code="\n".join(body) + "\n", skip=skip))
        i = end + 1
    return snippets


def _dedent(line: str, indent: int) -> str:
    """Remove up to `indent` leading spaces, as CommonMark does inside a fence."""
    removable = len(line) - len(line.lstrip(" "))
    return line[min(indent, removable) :]


def run_page(page: Path, timeout: float = DEFAULT_TIMEOUT) -> PageResult:
    """Run one Page's Snippets in order, in one shared namespace.

    The Page runs in a fresh Python process (the interpreter running
    docs-guardian, so the Guarded Project must be installed in its
    environment), with an empty temporary folder as its working directory, so
    it passes only if it works from a reader's blank folder.

    Args:
        page: The Markdown Page.
        timeout: Seconds the whole Page may run.

    Returns:
        The Page's result. A Snippet that raises, a timeout, or a process that
        exits without reporting back all fail the Page.
    """
    all_snippets = extract_snippets(page.read_text())
    snippets = [s for s in all_snippets if not s.skip]
    skipped = len(all_snippets) - len(snippets)
    request = {"page": str(page), "snippets": [[s.line, s.code] for s in snippets]}
    with (
        tempfile.TemporaryDirectory(prefix="docs-guardian-page-") as workdir,
        tempfile.TemporaryDirectory(prefix="docs-guardian-events-") as events_dir,
    ):
        events_file = Path(events_dir) / "events.jsonl"
        events_file.touch()
        timed_out, exit_code = False, None
        try:
            exit_code = subprocess.run(
                [sys.executable, "-m", "docs_guardian._worker", str(events_file)],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=timeout,
            ).returncode
        except subprocess.TimeoutExpired:  # the child has been killed
            timed_out = True
        events = [json.loads(line) for line in events_file.read_text().splitlines()]

    def failed_at(i: int, line: int, error: str) -> PageResult:
        return PageResult(
            page,
            ran=i,
            skipped=skipped,
            not_run=max(0, len(snippets) - i - 1),
            line=line,
            error=error,
        )

    failure = next((e for e in events if "failed" in e), None)
    if failure is not None:
        return failed_at(failure["failed"], failure["line"], failure["error"])
    if any("done" in e for e in events):
        return PageResult(page=page, ran=len(snippets), skipped=skipped)
    # No verdict from the worker: it was killed at the timeout, or it died.
    i = max((e["started"] for e in events if "started" in e), default=0)
    line = snippets[i].line if snippets else None
    if timed_out:
        return failed_at(i, line, f"Timeout: still running after {timeout:g}s")
    return failed_at(
        i, line, f"Crash: the Page's process exited with code {exit_code} before finishing"
    )


def run_pages(root: Path, timeout: float = DEFAULT_TIMEOUT) -> list[PageResult]:
    """Run every Markdown Page under a folder, one Page at a time.

    Args:
        root: Folder searched recursively for `*.md` Pages.
        timeout: Seconds each Page may run.

    Returns:
        One result per Page, in path order.
    """
    return [run_page(page, timeout) for page in sorted(Path(root).rglob("*.md"))]
