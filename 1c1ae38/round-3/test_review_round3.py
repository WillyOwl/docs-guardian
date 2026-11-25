"""Independent review probes against PR #11 at 1c1ae38; no implementation changes."""
import json
import os
from pathlib import Path
import subprocess
import textwrap

from markdown_it import MarkdownIt
import pytest

from docs_guardian.cli import main
from docs_guardian.drift import ApiChange, ChangeKind, Mention, find_mentions, render_report

ROOT = Path('/tmp/pr11-review-round3/source')
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


def test_private_module_changes_do_not_leak_into_report(guarded, capsys):
    (guarded / 'src/pkg/_internal.py').write_text('def hidden(x): ...\n')
    assert run_cli() == 0
    assert 'No API Changes.' in capsys.readouterr().out


def test_nested_pages_and_notebook_cells_have_stable_locations(guarded, capsys):
    (guarded / 'src/pkg/__init__.py').write_text(AFTER)
    nested = guarded / 'docs/deep'
    nested.mkdir()
    (nested / 'guide.md').write_text('> Example:\n>\n> ```python\n> pkg.convert(1)\n> ```\n')
    (nested / 'walk.ipynb').write_text(json.dumps({'cells': [
        {'cell_type': 'markdown', 'source': ['convert']},
        {'cell_type': 'code', 'source': ['value = 1\n', 'pkg.convert(value)']},
    ]}))
    assert run_cli() == 0
    report = capsys.readouterr().out
    assert 'Drift on 3 Pages' in report
    assert 'deep/guide.md:4' in report
    assert 'deep/walk.ipynb (cell 2, line 2)' in report


def test_unreadable_utf8_is_not_silent(guarded, capsys):
    (guarded / 'docs/latin1.md').write_bytes(b'caf\xe9 `convert`')
    assert run_cli() == 0
    report = capsys.readouterr().out
    assert 'Could not read' in report and 'latin1.md' in report


def test_invalid_base_still_reports_a_configuration_error(guarded, capsys):
    assert main(['drift', '--base', 'no-such-base', '--source', 'src', '--docs', 'docs']) == 2
    assert 'cannot find the merge base' in capsys.readouterr().err


def test_bad_source_syntax_is_advisory(guarded, capsys):
    (guarded / 'src/pkg/broken.py').write_text('def broken(:\n')
    assert run_cli() == 0
    report = capsys.readouterr().out
    assert 'Could not read' in report and 'pkg/broken.py' in report


def test_report_table_keeps_backticks_pipes_and_page_paths():
    report = render_report([
        ApiChange('fit', ChangeKind.CHANGED, ('(x: int | str)',), ("(x: int | str, sep='`')",)),
    ], {'fit': [Mention('nested/quick|start.md', 7), Mention('walk.ipynb', 2, 3)]},
        'main', '1234567')
    html = MarkdownIt('commonmark').enable('table').render(report)
    row = html.split('<tbody>')[1].split('</tr>')[0]
    assert row.count('<td>') == 3
    assert "(x: int | str, sep='`')" in html
    assert 'nested/quick|start.md:7' in html
    assert 'walk.ipynb (cell 3, line 2)' in html


def test_oversized_report_stays_under_comment_limit_and_points_to_summary(tmp_path):
    run, _ = workflow_case(tmp_path, 'new')
    assert run.returncode == 0
    report_path = tmp_path / 'drift-report.md'
    report_path.write_text(report_path.read_text() + ('A changed API: 中文\n' * 5_000))
    env = dict(os.environ, PATH=str(tmp_path / 'bin') + os.pathsep + os.environ['PATH'],
               MOCK_MODE='new', MOCK_CALLS=str(tmp_path / 'calls.jsonl'),
               GITHUB_REPOSITORY='WillyOwl/docs-guardian', PR='11', GITHUB_RUN_ID='local-review')
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', str(ROOT / '.github/scripts/post-drift-report.sh'),
                             str(report_path)], cwd=tmp_path, env=env, text=True, capture_output=True)
    assert result.returncode == 0
    body = (tmp_path / 'body.md').read_bytes().decode('utf-8', errors='replace')
    assert body.startswith('<!-- docs-guardian:drift-report changes=1 ')
    assert len(body) < 65_536
    assert 'truncated: the full report is in the job summary of run local-review' in body
