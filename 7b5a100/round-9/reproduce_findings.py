"""Reproduce each finding with the CLI in a disposable repository."""

import contextlib
import html
import io
import json
from pathlib import Path
import subprocess
import tempfile

import markdown

from docs_guardian.cli import main

HERE = Path(__file__).resolve().parent
SHA = '7b5a100481ec7a078551d307325c3f422f48793b'
PAGES = {
    'F1': '```python\nimport tinyml as tm\ntm.fit_linear(X, y)\n```\n',
    'F2': '!!! note\n\n    ```python\n    tinyml.fit_linear(X, y)\n    ```\n',
    'F3': 'Call `tinyml.fit_linear(X, y)`.\n',
    'F4': 'Call `tinyml.fit_linear(X, y)`.\n',
}


def git(root, *args):
    subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)


sections = []
for finding, page in PAGES.items():
    with tempfile.TemporaryDirectory(prefix=f'pr11-round9-{finding.lower()}-') as name:
        root = Path(name)
        (root / 'src/tinyml').mkdir(parents=True)
        (root / 'docs').mkdir()
        source = root / 'src/tinyml/__init__.py'
        source.write_text('def fit_linear(X, y): ...\n')
        if finding == 'F3':
            notebook = {'cells': [{'cell_type': 'markdown', 'source': [page], 'metadata': {}}],
                        'metadata': {}, 'nbformat': 4, 'nbformat_minor': 5}
            (root / 'docs/p.ipynb').write_text(json.dumps(notebook))
        else:
            (root / 'docs/p.md').write_text(page)
        git(root, 'init', '-q', '-b', 'main')
        git(root, 'config', 'user.name', 'Review fixture')
        git(root, 'config', 'user.email', 'review@example.invalid')
        git(root, 'add', '.')
        git(root, 'commit', '-qm', 'test: create baseline API')
        git(root, 'switch', '-qc', 'feature')
        if finding == 'F4':
            git(root, 'rm', 'src/tinyml/__init__.py')
            (root / 'src').mkdir(exist_ok=True)
        else:
            source.write_text('')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = main(['drift', '--base', 'main', '--source', str(root / 'src'),
                           '--docs', str(root / 'docs')])
        description = [
            f'{finding} | PR #11 review round 9 | reviewed commit {SHA}',
            'Setup: temporary git repo with fit_linear(X, y) at main; feature removes it.',
            'Page source' + (' (notebook Markdown cell 1):' if finding == 'F3' else ':'),
            page,
            '$ docs-guardian drift --base main --source <fixture>/src --docs <fixture>/docs',
            stdout.getvalue(), stderr.getvalue(),
            f'Actual CLI exit: {status}; expected: 0, with one API removal and one Drift Page.',
        ]
        if finding == 'F4':
            description.insert(2, 'Configured src directory still exists; its last Python module was deleted.')
        rendered = markdown.markdown(page, extensions=['admonition', 'pymdownx.superfences'])
        if finding == 'F2':
            description += ['Configured site renderer HTML (admonition + superfences):', rendered]
        output = '\n'.join(description).replace(str(root), '<fixture>') + '\n'
        (HERE / f'{finding.lower()}-reproduction.txt').write_text(output)
        print(output)
        sections.append(f'<h2>{finding}</h2><pre>{html.escape(page)}</pre>' + rendered)

(HERE / 'site-rendered-examples.html').write_text(
    '<!doctype html><meta charset="utf-8"><style>'
    'body{font:16px/1.5 sans-serif;max-width:1100px;margin:32px auto;color:#172135}'
    'pre{background:#eee;padding:20px;white-space:pre-wrap}'
    '.admonition{border:2px solid #2586c8;padding:16px}'
    '</style><h1>PR #11 / 7b5a100 / Review round 9</h1>'
    '<p>Page source and actual Python-Markdown output using the site extensions. '
    'F3 shows the contents of notebook Markdown cell 1.</p>' + ''.join(sections)
)
