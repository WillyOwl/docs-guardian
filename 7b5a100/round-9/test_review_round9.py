"""Review probes for the actual PR head; failures express required behavior."""

import json
import subprocess

import pytest

from docs_guardian.cli import main
from docs_guardian.drift import find_mentions


def git(root, *args):
    return subprocess.run(
        ['git', *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / 'src/tinyml').mkdir(parents=True)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'src/tinyml/__init__.py').write_text('def fit_linear(X, y): ...\n')
    (tmp_path / 'docs/p.md').write_text('Call `tinyml.fit_linear(X, y)`.\n')
    git(tmp_path, 'init', '-q', '-b', 'main')
    git(tmp_path, 'config', 'user.name', 'Review fixture')
    git(tmp_path, 'config', 'user.email', 'review@example.invalid')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'test: create baseline API')
    git(tmp_path, 'switch', '-qc', 'feature')
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_report(capsys):
    status = main(['drift', '--base', 'main', '--source', 'src', '--docs', 'docs'])
    captured = capsys.readouterr()
    return status, captured.out, captured.err


@pytest.mark.parametrize('code', [
    'import tinyml as tm\ntm.fit_linear(X, y)',
    'import tinyml.models as m\nm.fit_linear(X, y)',
    'from tinyml import models\nmodels.fit_linear(X, y)',
], ids=['package-alias', 'module-alias', 'from-import-module'])
def test_f1_module_alias_mentions_are_not_lost(repo, capsys, code):
    (repo / 'docs/p.md').write_text('```python\n' + code + '\n```\n')
    (repo / 'src/tinyml/__init__.py').write_text('')
    status, report, error = run_report(capsys)
    assert status == 0, error
    assert 'changes=1 drift-pages=1' in report, report
    assert '| `fit_linear` | removed | `p.md:3` |' in report


@pytest.mark.parametrize(('page', 'line'), [
    ('!!! note\n\n    ```python\n    tinyml.fit_linear(X, y)\n    ```\n', 4),
    ('!!! note\n\n    Call `tinyml.fit_linear(X, y)`.\n', 3),
], ids=['python-fence', 'inline-code'])
def test_f2_mentions_in_site_admonitions_are_not_lost(repo, capsys, page, line):
    (repo / 'docs/p.md').write_text(page)
    (repo / 'src/tinyml/__init__.py').write_text('')
    status, report, error = run_report(capsys)
    assert status == 0, error
    assert 'changes=1 drift-pages=1' in report, report
    assert f'| `fit_linear` | removed | `p.md:{line}` |' in report


def test_f3_notebook_markdown_inline_code_is_a_mention(repo, capsys):
    (repo / 'docs/p.md').write_text('Only prose.\n')
    (repo / 'docs/walk.ipynb').write_text(json.dumps({
        'cells': [{'cell_type': 'markdown', 'source': ['Call `tinyml.fit_linear(X, y)`.'],
                   'metadata': {}}],
        'metadata': {}, 'nbformat': 4, 'nbformat_minor': 5,
    }))
    (repo / 'src/tinyml/__init__.py').write_text('')
    status, report, error = run_report(capsys)
    assert status == 0, error
    assert 'changes=1 drift-pages=1' in report, report
    assert '`walk.ipynb (cell 1, line 1)`' in report


def test_f4_removing_the_last_module_reports_removals_and_stays_advisory(repo, capsys):
    git(repo, 'rm', 'src/tinyml/__init__.py')
    # Keep the configured source folder: the path itself was not mistyped.
    (repo / 'src').mkdir(exist_ok=True)
    status, report, error = run_report(capsys)
    assert status == 0, f'{error}\n{report}'
    assert 'changes=1 drift-pages=1' in report, report
    assert '| `fit_linear` | removed | `p.md:1` |' in report


def test_control_direct_qualified_mention_and_empty_module_work(repo, capsys):
    (repo / 'src/tinyml/__init__.py').write_text('')
    status, report, error = run_report(capsys)
    assert status == 0, error
    assert '| `fit_linear` | removed | `p.md:1` |' in report


def test_control_deleting_a_module_works_when_a_second_module_remains(repo, capsys):
    (repo / 'src/remaining.py').write_text('')
    git(repo, 'rm', 'src/tinyml/__init__.py')
    status, report, error = run_report(capsys)
    assert status == 0, error
    assert '| `fit_linear` | removed | `p.md:1` |' in report


def test_control_unrelated_object_and_prose_are_not_mentions(tmp_path):
    (tmp_path / 'p.md').write_text('fit_linear is prose.\n\n```python\nmodel.fit_linear(X, y)\n```\n')
    assert find_mentions(tmp_path, ['fit_linear'], packages=['tinyml']) == {'fit_linear': []}


def test_control_bare_and_notebook_code_mentions_work(tmp_path):
    (tmp_path / 'p.md').write_text('Call `fit_linear`.\n')
    (tmp_path / 'walk.ipynb').write_text(json.dumps({
        'cells': [{'cell_type': 'code', 'source': 'tinyml.fit_linear(X, y)'}],
    }))
    found = find_mentions(tmp_path, ['fit_linear'], packages=['tinyml'])
    assert [m.where for m in found['fit_linear']] == ['p.md:1', 'walk.ipynb (cell 1, line 1)']


def test_control_alias_import_is_valid_python():
    namespace = {}
    exec('import tinyml as tm\nf = tm.fit_linear', namespace)
    assert callable(namespace['f'])


def test_control_site_renders_admonition_fence_and_inline_code():
    markdown = pytest.importorskip('markdown')
    fence = markdown.markdown(
        '!!! note\n\n    ```python\n    tinyml.fit_linear(X, y)\n    ```\n',
        extensions=['admonition', 'pymdownx.superfences'],
    )
    inline = markdown.markdown('!!! note\n\n    Call `tinyml.fit_linear(X, y)`.\n',
                               extensions=['admonition', 'pymdownx.superfences'])
    assert 'admonition note' in fence and '<code>' in fence
    assert 'fit_linear' in fence
    assert '<code>tinyml.fit_linear(X, y)</code>' in inline
