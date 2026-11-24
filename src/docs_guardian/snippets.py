"""The snippet runner: run every Snippet of every Markdown Page, one Page per process."""

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

DEFAULT_TIMEOUT = 30.0
"""Seconds a Page may run before it fails with a Timeout."""

SKIP_MARKER = "<!-- docs-guardian: skip -->"
"""Put on the line directly above a fence to make that Snippet a Skipped Snippet."""

PYTHON_INFO_WORDS = frozenset({"python", "py", "python3"})
"""Info-string first words, case-insensitive, that make a fence a Snippet."""

# One CommonMark parser for every Page: Snippets are found the way a renderer
# finds them, inside lists and blockquotes, and never inside HTML comments.
_MARKDOWN = MarkdownIt("commonmark")


@dataclass(frozen=True)
class Snippet:
    """One fenced `python` block of a Page.

    Attributes:
        line: Line number in the Page of the Snippet's first code line.
        code: The Snippet's source, without the fence's indentation or quote markers.
        skip: True for a Skipped Snippet: the skip marker sits directly above its fence.
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

    The Page is parsed as CommonMark, so a Snippet is exactly a fenced code
    block a renderer would show: fences inside lists and blockquotes count,
    and fences inside HTML comments do not. A fence is a Snippet when its info
    string's first word is `python`, `py` or `python3`, in any case.

    Args:
        text: The Page's Markdown source.

    Returns:
        The Snippets in Page order, Skipped Snippets included.
    """
    tokens = _MARKDOWN.parse(text)
    # Lines where a skip-marker HTML block ends; a fence starting there is skipped.
    skip_marker_ends = {
        t.map[1] for t in tokens if t.type == "html_block" and t.content.strip() == SKIP_MARKER
    }
    snippets: list[Snippet] = []
    for token in tokens:
        words = token.info.split()
        if token.type != "fence" or not words or words[0].lower() not in PYTHON_INFO_WORDS:
            continue
        fence_line = token.map[0]  # 0-based line of the opening fence
        snippets.append(
            Snippet(line=fence_line + 2, code=token.content, skip=fence_line in skip_marker_ends)
        )
    return snippets


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
    finished = any("done" in e for e in events)
    if finished and not timed_out and exit_code == 0:
        return PageResult(page=page, ran=len(snippets), skipped=skipped)
    # No clean verdict: the process was killed at the timeout (possibly after its
    # last Snippet, kept alive by a thread or child process), or it died.
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
