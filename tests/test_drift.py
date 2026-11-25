import json
import subprocess
import textwrap
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from docs_guardian.cli import main
from docs_guardian.drift import (
    ApiChange,
    ChangeKind,
    Mention,
    api_changes,
    find_mentions,
    package_api,
    public_api,
    render_report,
)


def api(source: str) -> dict[str, frozenset[str]]:
    return public_api(textwrap.dedent(source))


def test_public_functions_are_keyed_by_name_with_their_full_signature():
    assert api(
        """
        def evaluate(y, y_pred, metric: str = "rmse") -> float: ...
        async def fetch(url, *, retries=3): ...
        """
    ) == {
        "evaluate": {"(y, y_pred, metric: str='rmse') -> float"},
        "fetch": {"(url, *, retries=3)"},
    }


def test_private_names_are_not_public_api():
    assert api(
        """
        def _helper(x): ...
        class _Hidden:
            def run(self): ...
        class Shown:
            def _private(self): ...
        """
    ) == {"Shown": {"()"}}


def test_a_class_is_keyed_by_its_init_and_its_public_methods_by_class_dot_name():
    assert api(
        """
        class LinearModel:
            def __init__(self, coef, intercept: float) -> None: ...
            def predict(self, X): ...
            def __repr__(self): ...
        """
    ) == {
        "LinearModel": {"(self, coef, intercept: float) -> None"},
        "LinearModel.predict": {"(self, X)"},
    }


def test_nested_definitions_and_other_statements_are_not_public_api():
    assert api(
        """
        import os
        X = 1
        def outer():
            def inner(): ...
        if True:
            def conditional(): ...
        """
    ) == {"outer": {"()"}}


def test_package_api_merges_public_modules_by_public_name():
    files = {
        "tinyml/__init__.py": "from tinyml.models import fit_linear\n",
        "tinyml/models.py": "def fit_linear(X, y): ...\n",
        "tinyml/_validation.py": "def as_target(values, name): ...\n",  # private module
        "tinyml/_data/loader.py": "def load(): ...\n",  # inside a private package
    }
    assert package_api(files) == {"fit_linear": {"(X, y)"}}


def test_moving_a_function_between_modules_is_not_an_api_change():
    before = package_api({"pkg/models.py": "def fit_linear(X, y): ...\n"})
    after = package_api({"pkg/linear.py": "def fit_linear(X, y): ...\n"})
    assert api_changes(before, after) == []


def test_api_changes_are_added_removed_or_changed_in_name_order():
    before = {"evaluate": {"(y, y_pred)"}, "fit_linear": {"(X, y)"}, "load_csv": {"(path)"}}
    after = {"evaluate": {"(y, y_pred, metric='rmse')"}, "fit": {"(X, y)"}, "load_csv": {"(path)"}}
    assert api_changes(before, after) == [
        ApiChange("evaluate", "changed", ("(y, y_pred)",), ("(y, y_pred, metric='rmse')",)),
        ApiChange("fit", "added", None, ("(X, y)",)),
        ApiChange("fit_linear", "removed", ("(X, y)",), None),
    ]


def mentions_in(tmp_path, pages: dict[str, str], names: list[str]) -> dict[str, list[str]]:
    for name, text in pages.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text)
    return {
        name: [m.where for m in found]
        for name, found in find_mentions(tmp_path, names, packages=["tinyml"]).items()
    }


def test_mentions_count_in_snippets_and_inline_code_but_never_in_prose(tmp_path):
    page = (
        "# Quickstart\n"  # 1
        "\n"  # 2
        "We fit_linear the data and evaluate it.\n"  # 3  prose: not a Mention
        "\n"  # 4
        "```python\n"  # 5
        "model = fit_linear(X, y)\n"  # 6
        "fit_linear_v2 = None\n"  # 7  a different name
        "```\n"  # 8
        "\n"  # 9
        "Then call `evaluate` on the\n"  # 10
        "predictions, or `tinyml.fit_linear`.\n"  # 11
    )
    assert mentions_in(tmp_path, {"quickstart.md": page}, ["fit_linear", "evaluate"]) == {
        "fit_linear": ["quickstart.md:6", "quickstart.md:11"],
        "evaluate": ["quickstart.md:10"],
    }


def test_a_method_is_mentioned_where_it_is_called_as_an_attribute(tmp_path):
    page = "Predict the price.\n\n```python\ny_pred = model.predict(X)\n```\n"
    found = mentions_in(tmp_path, {"api/models.md": page}, ["LinearModel.predict"])
    assert found == {"LinearModel.predict": ["api/models.md:4"]}


def test_mentions_in_notebook_code_cells_but_not_markdown_cells(tmp_path):
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["We call fit_linear here."], "metadata": {}},
            {
                "cell_type": "code",
                "source": ["X, y = housing()\n", "m = fit_linear(X, y)"],
                "metadata": {},
                "outputs": [],
                "execution_count": None,
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    found = mentions_in(tmp_path, {"nb/walk.ipynb": json.dumps(notebook)}, ["fit_linear"])
    assert found == {"fit_linear": ["nb/walk.ipynb (cell 2, line 2)"]}


def test_a_name_with_no_mentions_maps_to_an_empty_list(tmp_path):
    assert mentions_in(tmp_path, {"a.md": "nothing here\n"}, ["fit"]) == {"fit": []}


# --- End to end: `docs-guardian drift` on a real git repo -------------------


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo whose `main` has a tiny package and a Page that uses it."""
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "src/pkg").mkdir(parents=True)
    (tmp_path / "src/pkg/__init__.py").write_text(
        "def fit_linear(X, y): ...\ndef evaluate(y, y_pred) -> float: ...\n"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/quickstart.md").write_text(
        "# Quickstart\n\n```python\nm = fit_linear(X, y)\nprint(evaluate(y, m))\n```\n"
    )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "feature")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_drift(capsys) -> tuple[int, str]:
    code = main(["drift", "--base", "main", "--source", "src", "--docs", "docs"])
    return code, capsys.readouterr().out


def test_drift_report_lists_drift_and_undocumented_additions(repo, capsys):
    (repo / "src/pkg/__init__.py").write_text(
        "def fit(X, y): ...\ndef evaluate(y, y_pred, metric='rmse') -> float: ...\n"
    )
    code, report = run_drift(capsys)
    assert code == 0  # Advisory: never fails the build
    assert "<!-- docs-guardian:drift-report changes=3 drift-pages=1 -->" in report
    assert "3 API Changes; Drift on 1 Page." in report
    assert (
        "| `evaluate` | `(y, y_pred) -> float` → `(y, y_pred, metric='rmse') -> float` "
        "| `quickstart.md:5` |" in report
    )
    assert "| `fit_linear` | removed | `quickstart.md:4` |" in report
    assert "**Not yet documented**: no Page Mentions `fit`." in report


def test_api_changes_that_no_page_mentions_are_not_drift(repo, capsys):
    (repo / "src/pkg/__init__.py").write_text(
        "def fit_linear(X, y): ...\ndef evaluate(y, y_pred) -> float: ...\ndef score(y): ...\n"
    )
    (repo / "docs/quickstart.md").write_text("```python\nscore(y)\n```\n")  # documented at once
    code, report = run_drift(capsys)
    assert code == 0
    assert "changes=1 drift-pages=0" in report
    assert "1 API Change; no Drift." in report


def test_no_api_changes_says_so(repo, capsys):
    (repo / "src/pkg/__init__.py").write_text(  # reformatted, same API
        "def fit_linear(X,   y): ...\n\n\ndef evaluate(y, y_pred) -> float:\n    return 0.0\n"
    )
    code, report = run_drift(capsys)
    assert code == 0
    assert "changes=0 drift-pages=0" in report
    assert "No API Changes." in report


# --- Review round 1 -----------------------------------------------------------


def test_the_same_name_in_two_modules_is_compared_in_full():
    before = package_api(
        {"p/m.py": "def evaluate(y): ...\n", "p/n.py": "def evaluate(a, b): ...\n"}
    )
    after = package_api(
        {"p/m.py": "def evaluate(y, z): ...\n", "p/n.py": "def evaluate(a, b): ...\n"}
    )
    [change] = api_changes(before, after)
    assert (change.name, change.kind) == ("evaluate", "changed")


def test_a_top_level_name_is_not_mentioned_by_a_same_named_method(tmp_path):
    page = "```python\nmodel.fit(x)\nimport tinyml\ntinyml.fit(x)\nfit(x)\n```\n"
    (tmp_path / "a.md").write_text(page)
    found = find_mentions(tmp_path, ["fit"], packages=["tinyml"])
    assert [m.where for m in found["fit"]] == ["a.md:4", "a.md:5"]


def test_unreadable_source_files_and_pages_become_notes_not_failures(repo, capsys):
    (repo / "src/pkg/broken.py").write_text("def oops(:\n")
    (repo / "docs/latin1.md").write_bytes("caf\xe9 `fit_linear`\n".encode("latin-1"))
    (repo / "docs/bad.ipynb").write_text("{not json")
    code, report = run_drift(capsys)
    assert code == 0  # Advisory, even when the PR contains unparseable files
    assert "Could not read" in report
    assert "`pkg/broken.py`" in report
    assert "`latin1.md`" in report and "`bad.ipynb`" in report


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--base", "no-such-branch"], "no-such-branch"),
        (["--source", "srcc"], "no Python files under srcc"),
        (["--docs", "doc"], "no Pages under doc"),
    ],
    ids=["unknown-base", "mistyped-source", "mistyped-docs"],
)
def test_a_misconfigured_run_exits_2_instead_of_reporting_nothing(repo, capsys, args, message):
    argv = dict(zip(["--base", "--source", "--docs"], ["main", "src", "docs"], strict=True))
    argv.update(dict(zip(args[::2], args[1::2], strict=True)))
    code = main(["drift", *[part for pair in argv.items() for part in pair]])
    assert code == 2
    assert message in capsys.readouterr().err


def test_output_writes_the_same_report_to_a_file(repo, capsys):
    code = main(
        ["drift", "--base", "main", "--source", "src", "--docs", "docs", "--output", "r.md"]
    )
    assert code == 0
    assert (repo / "r.md").read_text() == capsys.readouterr().out


def test_drift_is_counted_in_pages(repo, capsys):
    (repo / "docs/tutorial.md").write_text("```python\nfit_linear(X, y)\n```\n")
    (repo / "src/pkg/__init__.py").write_text("def evaluate(y, y_pred) -> float: ...\n")
    _, report = run_drift(capsys)
    assert "changes=1 drift-pages=2" in report
    assert "1 API Change; Drift on 2 Pages." in report


# --- Review round 2 -----------------------------------------------------------


def test_a_change_inside_union_annotations_is_an_api_change(repo, capsys):
    before = "def convert(value: int | str | bytes) -> float | bool | None: ...\n"
    after = "def convert(value: int | bool | bytes) -> float | str | None: ...\n"
    (repo / "src/pkg/__init__.py").write_text(before)
    git(repo, "commit", "-qam", "unions")
    git(repo, "branch", "-qf", "main")
    (repo / "src/pkg/__init__.py").write_text(after)
    _, report = run_drift(capsys)
    assert "changes=1 " in report
    assert (  # pipes escaped, so GitHub keeps the table cells (see the next test)
        r"`(value: int \| str \| bytes) -> float \| bool \| None` → "
        r"`(value: int \| bool \| bytes) -> float \| str \| None`" in report
    )


def test_pipes_and_backticks_in_signatures_keep_every_table_cell():
    change = ApiChange("fit", ChangeKind.CHANGED, ("(x: int | str)",), ("(x: int | str, sep='`')",))
    report = render_report([change], {"fit": [Mention("quick|start.md", 2)]}, "main", "1234567")
    html = MarkdownIt("commonmark").enable("table").render(report)
    row = html.split("<tbody>")[1].split("</tr>")[0]
    assert row.count("<td>") == 3
    assert "<code>(x: int | str)</code>" in row
    assert "<code>(x: int | str, sep='`')</code>" in row
    assert "<code>quick|start.md:2</code>" in row


@pytest.mark.parametrize(
    "notebook",
    [
        {"cells": None},
        [],
        {"cells": [None]},
        {"cells": [{"cell_type": "code", "source": 3}]},
        {"cells": [{"cell_type": "code", "source": ["x = 1\n", 2]}]},
    ],
    ids=["null-cells", "not-an-object", "null-cell", "int-source", "non-string-line"],
)
def test_valid_json_that_is_not_a_notebook_becomes_a_note(repo, capsys, notebook):
    (repo / "docs/broken.ipynb").write_text(json.dumps(notebook))
    code, report = run_drift(capsys)
    assert code == 0
    assert "**Could not read**" in report and "`broken.ipynb`" in report


def test_folders_named_like_pages_or_modules_are_not_read(repo, capsys):
    (repo / "docs/guide.md").mkdir()
    (repo / "src/pkg/legacy.py").mkdir()
    code, report = run_drift(capsys)
    assert code == 0
    assert "No API Changes." in report


def test_an_inline_mention_is_located_on_its_own_line_not_on_earlier_prose(tmp_path):
    page = (
        "We evaluate the model.\n"  # 1  prose
        "Then call `evaluate`.\n"  # 2
        "\n"
        "- a list item that spans `a\n"  # 4  a code span over two lines
        "  b`, then `evaluate` again.\n"  # 5
        "\n"
        "> evaluate in a quote, and\n"  # 7
        "> [`evaluate`](api.md) as a link.\n"  # 8
    )
    assert mentions_in(tmp_path, {"guide.md": page}, ["evaluate"]) == {
        "evaluate": ["guide.md:2", "guide.md:5", "guide.md:8"]
    }
