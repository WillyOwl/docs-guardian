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
