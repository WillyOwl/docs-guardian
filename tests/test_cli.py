from docs_guardian.cli import main


def test_snippets_exits_1_and_names_the_failing_line(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/ok.md").write_text("```python\nx = 1\n```\n")
    (tmp_path / "docs/broken.md").write_text(
        "# Broken\n\n```python\nfit_linear()\n```\n\n```python\nprint(1)\n```\n"
    )
    assert main(["snippets", "docs"]) == 1
    out = capsys.readouterr().out
    assert "FAIL docs/broken.md:4  NameError: name 'fit_linear' is not defined" in out
    assert "(1 Snippet not run)" in out
    assert "PASS docs/ok.md" in out
    assert "2 Pages: 1 passed, 1 failed" in out


def test_snippets_exits_0_when_every_page_passes(tmp_path, capsys):
    (tmp_path / "ok.md").write_text("```python\nx = 1\n```\n")
    assert main(["snippets", str(tmp_path)]) == 0
    assert "1 Page: 1 passed, 0 failed" in capsys.readouterr().out


def test_snippets_exits_2_when_the_folder_has_no_pages(tmp_path, capsys):
    # A mistyped path in a workflow must not pass silently.
    assert main(["snippets", str(tmp_path / "doc")]) == 2
    assert "no Markdown Pages under" in capsys.readouterr().err
