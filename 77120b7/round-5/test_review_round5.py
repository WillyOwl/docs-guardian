"""Independent expected-behavior probes for PR #11 at 77120b7.

These are review evidence only, not changes to the implementation branch.
"""
import subprocess
from pathlib import Path

import pytest

from docs_guardian.cli import main
from docs_guardian.drift import api_changes, public_api


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


@pytest.fixture
def guarded(tmp_path, monkeypatch):
    git(tmp_path, 'init', '-q', '-b', 'main')
    git(tmp_path, 'config', 'user.email', 'review@example.invalid')
    git(tmp_path, 'config', 'user.name', 'Review fixture')
    (tmp_path / 'src/pkg').mkdir(parents=True)
    (tmp_path / 'src/pkg/__init__.py').write_text('def fit(x): ...\n')
    (tmp_path / 'src/other').mkdir()
    (tmp_path / 'src/other/__init__.py').write_text('def unrelated(): ...\n')
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/guide.md').write_text('```python\nimport pkg\npkg.fit(1)\n```\n')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-qm', 'test: seed guarded project')
    git(tmp_path, 'switch', '-qc', 'feature')
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_cli(source='src'):
    return main(['drift', '--base', 'main', '--source', source, '--docs', 'docs'])


OVERLOADED = '''from typing import overload
class Estimator:
    @overload
    def __init__(self, value: int) -> None: ...
    @overload
    def __init__(self, value: str) -> None: ...
    def __init__(self, value):
        self.value = value
'''


def test_r5_f1_second_constructor_overload_change_is_reported(guarded, capsys):
    module = guarded / 'src/pkg/__init__.py'
    module.write_text(OVERLOADED)
    (guarded / 'docs/guide.md').write_text('Create `Estimator("sample")`.\n')
    git(guarded, 'add', '.')
    git(guarded, 'commit', '-qm', 'test: add constructor overloads')
    git(guarded, 'branch', '-f', 'main')
    module.write_text(OVERLOADED.replace('value: str', 'value: bytes'))
    assert run_cli() == 0
    report = capsys.readouterr().out
    print(report)
    assert 'changes=1 drift-pages=1' in report
    assert '| `Estimator` |' in report


def test_r5_f1_constructor_implementation_signature_change_is_reported():
    before = public_api(OVERLOADED)
    after = public_api(OVERLOADED.replace('def __init__(self, value):',
                                         'def __init__(self, value, *, strict=False):'))
    print('Before:', before)
    print('After:', after)
    changes = api_changes(before, after)
    assert len(changes) == 1 and changes[0].name == 'Estimator'


def test_r5_f2_removed_package_qualified_mention_still_counts(guarded, capsys):
    (guarded / 'src/pkg/__init__.py').unlink()
    (guarded / 'src/pkg').rmdir()
    assert run_cli() == 0
    report = capsys.readouterr().out
    print(report)
    assert 'changes=1 drift-pages=1' in report
    assert '| `fit` | removed | `guide.md:3` |' in report


def test_r5_f2_namespace_package_qualified_mention_counts(guarded, capsys):
    (guarded / 'src/pkg/ops.py').write_text('def fit(x): ...\n')
    (guarded / 'src/pkg/__init__.py').unlink()
    (guarded / 'docs/guide.md').write_text('Call `pkg.ops.fit(1)`.\n')
    git(guarded, 'add', '.')
    git(guarded, 'commit', '-qm', 'test: use a namespace package')
    git(guarded, 'branch', '-f', 'main')
    (guarded / 'src/pkg/ops.py').write_text('def fit(x, *, retries=3): ...\n')
    assert run_cli() == 0
    report = capsys.readouterr().out
    print(report)
    assert 'changes=1 drift-pages=1' in report
    assert '`guide.md:1`' in report


def test_control_non_overloaded_constructor_changes_are_detected():
    before = public_api('class Estimator:\n def __init__(self, value: str): ...\n')
    after = public_api('class Estimator:\n def __init__(self, value: bytes): ...\n')
    assert len(api_changes(before, after)) == 1


def test_control_removing_function_from_existing_package_counts(guarded, capsys):
    (guarded / 'src/pkg/__init__.py').write_text('')
    assert run_cli() == 0
    report = capsys.readouterr().out
    assert 'changes=1 drift-pages=1' in report
    assert '`guide.md:3`' in report


def test_control_regular_package_qualified_mention_counts(guarded, capsys):
    (guarded / 'src/pkg/__init__.py').write_text('def fit(x, *, retries=3): ...\n')
    assert run_cli() == 0
    assert 'changes=1 drift-pages=1' in capsys.readouterr().out
