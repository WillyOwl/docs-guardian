"""Review-only expected-behavior probes; intentionally fail on PR #11 at 39c7d29."""
import json
import os
from pathlib import Path
import subprocess
import textwrap

from markdown_it import MarkdownIt
import pytest

from docs_guardian.cli import main
from docs_guardian.drift import ApiChange, ChangeKind, Mention, find_mentions, render_report

ROOT = Path('/home/yiyang/docs-guardian')
BEFORE = 'def convert(value: int | str | bytes) -> float | bool | None: ...\n'
AFTER = 'def convert(value: int | bool | bytes) -> float | str | None: ...\n'

@pytest.fixture
def guarded(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)
    git('init', '-q', '-b', 'baseline')
    git('config', 'user.name', 'Review fixture')
    git('config', 'user.email', 'review@example.invalid')
    (tmp_path / 'src/pkg').mkdir(parents=True)
    (tmp_path / 'src/pkg/__init__.py').write_text(BEFORE)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs/quickstart.md').write_text('```python\nconvert(value)\n```\n')
    git('add', '.')
    git('commit', '-qm', 'test: create review fixture')
    git('switch', '-qc', 'test/review-fixture')
    monkeypatch.chdir(tmp_path)
    return tmp_path

def run_cli():
    return main(['drift', '--base', 'baseline', '--source', 'src', '--docs', 'docs'])

def test_union_annotation_changes_are_reported(guarded, capsys):
    (guarded / 'src/pkg/__init__.py').write_text(AFTER)
    assert run_cli() == 0
    report = capsys.readouterr().out
    print('BEFORE:', BEFORE.strip(), '\nAFTER:', AFTER.strip(), '\nOBSERVED:\n', report)
    assert 'changes=1 ' in report, 'real parameter and return annotation changes were lost'

def test_malformed_notebook_is_advisory(guarded, capsys):
    (guarded / 'docs/broken.ipynb').write_text(json.dumps({'cells': None}))
    result = run_cli()
    report = capsys.readouterr().out
    assert result == 0
    assert 'Could not read' in report and 'broken.ipynb' in report

def test_inline_code_location_skips_preceding_prose(tmp_path):
    (tmp_path / 'guide.md').write_text('We evaluate the model.\nThen call `evaluate`.\n')
    found = [m.where for m in find_mentions(tmp_path, ['evaluate'])['evaluate']]
    print('PAGE:\n1: We evaluate the model.\n2: Then call `evaluate`.\nOBSERVED:', found)
    assert found == ['guide.md:2']

def test_union_signature_keeps_the_pages_table_cell():
    report = render_report(
        [ApiChange('fit', ChangeKind.CHANGED, ('(x: int | str)',), ('(x: int | str, y=0)',))],
        {'fit': [Mention('quickstart.md', 2)]}, 'main', '1234567',
    )
    html = MarkdownIt('commonmark').enable('table').render(report)
    print('RAW REPORT:\n', report, '\nRENDERED HTML:\n', html)
    assert 'quickstart.md:2' in html, 'unescaped union pipes discard the Pages column'

def workflow_case(tmp_path, mode, changes=1):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / 'post-comment.sh').write_text((ROOT / '.github/scripts/post-drift-report.sh').read_text())
    (tmp_path / 'drift-report.md').write_text(
        f'<!-- docs-guardian:drift-report changes={changes} drift-pages=0 -->\n### Drift Report\n'
    )
    stub = tmp_path / 'bin/gh'
    stub.parent.mkdir()
    stub.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['MOCK_CALLS'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
mode = os.environ['MOCK_MODE']
if '-X' not in args:
    if mode == 'list-error':
        print('gh: HTTP 503 Service Unavailable', file=sys.stderr)
        sys.exit(1)
    if mode in ('rewrite', 'rewrite-zero'):
        print('12345')
elif mode == 'post-forbidden':
    print('gh: HTTP 403 Resource not accessible by integration', file=sys.stderr)
    sys.exit(1)
''')
    stub.chmod(0o755)
    env = dict(os.environ, PATH=str(stub.parent) + os.pathsep + os.environ['PATH'],
               MOCK_MODE=mode, MOCK_CALLS=str(tmp_path / 'calls.jsonl'),
               GITHUB_REPOSITORY='WillyOwl/docs-guardian', PR='11',
               GITHUB_RUN_ID='local-review', GH_TOKEN='fake-token-not-used')
    run = subprocess.run(['bash', '-e', '-o', 'pipefail', 'post-comment.sh', 'drift-report.md'],
                         cwd=tmp_path, env=env, text=True, capture_output=True)
    calls = [json.loads(line) for line in (tmp_path / 'calls.jsonl').read_text().splitlines()]
    return run, calls

def test_comment_lookup_failure_is_advisory(tmp_path):
    run, calls = workflow_case(tmp_path, 'list-error')
    print('MOCKED CALLS:', calls, '\nSTDOUT:', run.stdout, '\nSTDERR:', run.stderr,
          '\nOBSERVED EXIT:', run.returncode)
    assert run.returncode == 0, 'comment lookup failure makes the Advisory workflow fail'
    assert '::warning::' in run.stdout

@pytest.mark.parametrize(('mode', 'changes', 'method'), [
    ('no-changes', 0, None),
    ('new', 1, 'POST'),
    ('rewrite', 1, 'PATCH'),
    ('rewrite-zero', 0, 'PATCH'),
    ('post-forbidden', 1, 'POST'),
])
def test_comment_workflow_existing_paths(tmp_path, mode, changes, method):
    run, calls = workflow_case(tmp_path, mode, changes)
    mutations = [call for call in calls if '-X' in call]
    print(mode, 'exit:', run.returncode, 'calls:', calls, 'output:', run.stdout.strip())
    assert run.returncode == 0
    assert [call[call.index('-X') + 1] for call in mutations] == ([] if method is None else [method])
    if mode == 'post-forbidden':
        assert '::warning::' in run.stdout
