import os
import signal
import time
from pathlib import Path

import pytest

from docs_guardian.snippets import extract_snippets, run_pages


def write_page(root: Path, name: str, text: str) -> Path:
    page = root / name
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(text)
    return page


def test_snippets_on_a_page_share_one_namespace(tmp_path):
    write_page(
        tmp_path,
        "tutorial.md",
        "# Tutorial\n\n```python\nx = 2\n```\n\nThen:\n\n```python\nassert x * 3 == 6\n```\n",
    )
    [result] = run_pages(tmp_path)
    assert result.passed
    assert (result.ran, result.skipped, result.not_run) == (2, 0, 0)


@pytest.mark.parametrize("info", ["python", "py", "python3", "Python", "python\ttitle='x'"])
def test_common_python_info_strings_are_snippets(info):
    # A Snippet the runner silently misses is a Page that is never tested.
    [snippet] = extract_snippets(f"```{info}\nx = 1\n```\n")
    assert snippet.code == "x = 1\n"


def test_non_python_fences_are_not_snippets():
    assert extract_snippets("```bash\nls\n```\n\n```\nplain\n```\n\n```pycon\n>>> 1\n```\n") == []


def test_a_fence_closes_only_on_a_matching_fence():
    text = '````python\ns = """\n```\n"""\nassert s == "\\n```\\n"\n````\n'
    [snippet] = extract_snippets(text)
    assert snippet.code == 's = """\n```\n"""\nassert s == "\\n```\\n"\n'


def test_pages_cannot_see_each_others_names(tmp_path):
    write_page(tmp_path, "a.md", "```python\nshared = 1\n```\n")
    write_page(tmp_path, "b.md", "```python\nprint(shared)\n```\n")
    a, b = run_pages(tmp_path)
    assert a.passed
    assert b.error == "NameError: name 'shared' is not defined"


def test_a_page_runs_in_an_empty_folder_like_a_readers(tmp_path):
    write_page(tmp_path, "data.csv", "a,b\n1,2\n")
    write_page(
        tmp_path, "page.md", "```python\nimport os\nassert os.listdir() == [], os.listdir()\n```\n"
    )
    [result] = run_pages(tmp_path)
    assert result.passed, result.error


def test_a_hanging_snippet_fails_its_page_at_the_timeout(tmp_path):
    write_page(
        tmp_path,
        "slow.md",
        "```python\nx = 1\n```\n\n"
        "```python\nimport time\ntime.sleep(60)\n```\n\n"
        "```python\nx\n```\n",
    )
    [result] = run_pages(tmp_path, timeout=1)
    assert not result.passed
    assert result.line == 6  # the Snippet that was running
    assert result.error == "Timeout: still running after 1s"
    assert (result.ran, result.not_run) == (1, 1)


def test_a_page_whose_process_dies_fails_rather_than_passes(tmp_path):
    write_page(
        tmp_path,
        "dies.md",
        "```python\nimport os\nos._exit(0)\n```\n\n"
        "```python\nraise RuntimeError('unreached')\n```\n",
    )
    [result] = run_pages(tmp_path)
    assert not result.passed
    assert result.line == 2
    assert result.error == "Crash: the Page's process exited with code 0 before finishing"
    assert (result.ran, result.not_run) == (0, 1)


def test_a_skipped_snippet_does_not_run(tmp_path):
    write_page(
        tmp_path,
        "page.md",
        "```python\nx = 1\n```\n\n"
        "<!-- docs-guardian: skip -->\n```python\nraise RuntimeError('needs network')\n```\n\n"
        "```python\nassert x == 1\n```\n",
    )
    [result] = run_pages(tmp_path)
    assert result.passed
    assert (result.ran, result.skipped) == (2, 1)


def test_a_failure_points_at_the_exact_line_and_counts_snippets_not_run(tmp_path):
    write_page(
        tmp_path,
        "quickstart.md",
        "\n".join(
            [
                "# Quickstart",  # 1
                "",  # 2
                "```python",  # 3
                "a = 1",  # 4
                "b = a + 1",  # 5
                "c = fit_linear(a, b)",  # 6  <- fails here
                "```",  # 7
                "",  # 8
                "```python",  # 9
                "print(c)",  # 10
                "```",  # 11
                "",  # 12
                "```python",  # 13
                "print('never')",  # 14
                "```",  # 15
            ]
        ),
    )
    [result] = run_pages(tmp_path)
    assert not result.passed
    assert result.line == 6
    assert result.error == "NameError: name 'fit_linear' is not defined"
    assert (result.ran, result.not_run) == (0, 2)


def test_an_exception_without_a_message_reports_just_its_type(tmp_path):
    write_page(tmp_path, "page.md", "```python\nraise RuntimeError()\n```\n")
    [result] = run_pages(tmp_path)
    assert result.error == "RuntimeError"


# --- Regressions from the PR #8 review -------------------------------------


@pytest.mark.parametrize(
    "markdown",
    [
        "- Example:\n\n    ```python\n    x = 1\n    raise RuntimeError('nested')\n    ```\n",
        "> ```python\n> x = 1\n> raise RuntimeError('nested')\n> ```\n",
        "1. Step one:\n\n   ```python\n   x = 1\n   raise RuntimeError('nested')\n   ```\n",
    ],
    ids=["bullet-list", "blockquote", "ordered-list"],
)
def test_snippets_nested_in_lists_and_blockquotes_run_and_point_at_their_line(tmp_path, markdown):
    write_page(tmp_path, "nested.md", markdown)
    [result] = run_pages(tmp_path)
    assert result.error == "RuntimeError: nested"  # was: PASS, 0 Snippets
    raising_line = next(n for n, line in enumerate(markdown.splitlines(), 1) if "raise" in line)
    assert result.line == raising_line


def test_a_skip_marker_inside_a_list_still_skips(tmp_path):
    write_page(
        tmp_path,
        "nested.md",
        "- Example:\n\n"
        "  <!-- docs-guardian: skip -->\n  ```python\n  raise RuntimeError()\n  ```\n",
    )
    [result] = run_pages(tmp_path)
    assert result.passed
    assert (result.ran, result.skipped) == (0, 1)


def test_fences_inside_an_html_comment_are_not_snippets(tmp_path):
    write_page(
        tmp_path, "draft.md", "<!--\n```python\nraise RuntimeError('hidden draft')\n```\n-->\n"
    )
    [result] = run_pages(tmp_path)
    assert result.passed
    assert result.ran == 0


def test_a_page_killed_at_the_timeout_fails_even_after_its_snippets_finished(tmp_path):
    # A non-daemon thread keeps the process alive after the last Snippet.
    write_page(
        tmp_path,
        "thread.md",
        "```python\nimport threading, time\n"
        "threading.Thread(target=lambda: time.sleep(60)).start()\n```\n",
    )
    [result] = run_pages(tmp_path, timeout=1)
    assert not result.passed  # was: PASS
    assert result.error == "Timeout: still running after 1s"


def test_a_syntax_error_points_at_the_broken_line(tmp_path):
    write_page(
        tmp_path, "syntax.md", "# Syntax\n\n```python\na = 1\nb = 2\nif True print(a)\n```\n"
    )
    [result] = run_pages(tmp_path)
    assert result.line == 6  # was: 4, the Snippet's first line
    assert result.error.startswith("SyntaxError: ")
    assert "syntax.md" not in result.error  # the location is already in result.line


# --- Regressions from the second PR #8 review (on 27b8353) -----------------


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_binary_output_neither_fails_the_page_nor_stops_the_run(tmp_path, stream):
    snippet = f"import sys\nsys.{stream}.buffer.write(bytes([255]))\n"
    write_page(tmp_path, "a-binary.md", f"```python\n{snippet}```\n")
    write_page(tmp_path, "b-next.md", "```python\nx = 1\n```\n")
    results = run_pages(tmp_path)  # was: UnicodeDecodeError escaping run_pages
    assert [(r.page.name, r.passed) for r in results] == [
        ("a-binary.md", True),
        ("b-next.md", True),
    ]


def _background_child_snippet(tmp_path: Path, then: str) -> tuple[str, Path, Path]:
    """A Snippet that starts a child which writes a marker after 1s, then does `then`."""
    pid_file, marker = tmp_path / "child.pid", tmp_path / "child-outlived-page"
    child = (
        "import os, time, pathlib; "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())); "
        f"time.sleep(1); pathlib.Path({str(marker)!r}).write_text('alive')"
    )
    snippet = (
        f"import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', {child!r}])\n{then}"
    )
    return snippet, pid_file, marker


def _kill_if_alive(pid_file: Path) -> None:
    if pid_file.exists():
        try:
            os.kill(int(pid_file.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            pass


@pytest.mark.parametrize(
    ("then", "timeout", "error"),
    [
        ("time.sleep(30)\n", 0.5, "Timeout: still running after 0.5s"),  # killed at the timeout
        ("time.sleep(0.3)\n", 30, None),  # finished normally, child still running
    ],
    ids=["page-times-out", "page-finishes"],
)
def test_no_process_started_by_a_page_outlives_it(tmp_path, then, timeout, error):
    snippet, pid_file, marker = _background_child_snippet(tmp_path, then)
    write_page(tmp_path, "child.md", f"```python\n{snippet}```\n")
    try:
        start = time.monotonic()
        [result] = run_pages(tmp_path, timeout=timeout)
        assert result.error == error
        assert pid_file.exists(), "the child must have started for this test to mean anything"
        while time.monotonic() < start + 1.6 and not marker.exists():
            time.sleep(0.05)
        assert not marker.exists(), "a process started by the Page kept running after it"
    finally:
        _kill_if_alive(pid_file)
