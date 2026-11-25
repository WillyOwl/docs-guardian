"""Produce a real CLI report from an isolated Guarded Project fixture."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from docs_guardian.cli import main

OUT = Path(__file__).resolve().parent

with TemporaryDirectory(prefix='pr11-review-demo-') as temp:
    root = Path(temp)
    def git(*args):
        return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True).stdout
    git('init', '-q', '-b', 'main')
    git('config', 'user.name', 'Review fixture')
    git('config', 'user.email', 'review@example.invalid')
    (root / 'src/pkg').mkdir(parents=True)
    source = root / 'src/pkg/__init__.py'
    source.write_text('def fit(x: int | str): ...\ndef old(x): ...\n')
    (root / 'docs').mkdir()
    (root / 'docs/quick|start.md').write_text('```python\nfit(1)\nold(1)\n```\n')
    (root / 'docs/walk.ipynb').write_text(json.dumps({'cells': [
        {'cell_type': 'markdown', 'source': ['Notebook walkthrough']},
        {'cell_type': 'code', 'source': ['fit(2)\n']},
    ]}))
    git('add', '.')
    git('commit', '-qm', 'test: create isolated report fixture')
    source.write_text('def fit(x: int | str, sep="`"): ...\ndef added(x): ...\n')
    os.chdir(root)
    output = io.StringIO()
    with redirect_stdout(output):
        status = main(['drift', '--base', 'main', '--source', 'src', '--docs', 'docs',
                       '--output', str(OUT / 'report-demo.md')])
    assert status == 0
    report = output.getvalue()
    assert 'changes=3 drift-pages=2' in report
    assert 'quick\\|start.md:2' in report and 'walk.ipynb (cell 2, line 1)' in report
    assert '**Not yet documented**: no Page Mentions `added`.' in report
    print('Isolated fixture: changed fit (union annotation + backtick default), removed old, added added.')
    print('Two Pages: quick|start.md and a notebook. No source files in the PR checkout were edited.')
    print(report, end='')
