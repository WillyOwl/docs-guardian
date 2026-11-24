"""Render unedited test logs as local HTML for actual browser screenshots."""
import html
import json
from pathlib import Path

out = Path(__file__).resolve().parent
commit = '27b835360c9e8dc530f842b780ee14ccf73e9f26'
style = '''
* { box-sizing: border-box; }
body { margin: 0; padding: 28px; background: #101820; color: #e8edf2;
       font-family: Arial, sans-serif; }
h1 { font-size: 26px; margin: 0 0 12px; } h2 { font-size: 20px; margin: 24px 0 12px; }
.meta { font: 15px/1.5 monospace; color: #acbed1; }
pre { background: #192530; border: 1px solid #3c4b5a; padding: 18px;
      border-radius: 6px; font: 14px/21px "DejaVu Sans Mono", monospace;
      white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; }
'''
groups = [
    ('tests', 'PR #8 | repository tests on Python 3.11 and 3.14', [
        ('Python 3.14.6 | 56 passed', 'pytest-3.14'),
        ('Python 3.11.15 | 56 passed (uv --python 3.11 --isolated)', 'pytest-3.11'),
    ]),
    ('quality-and-pages', 'PR #8 | lint, Markdown, notebook and strict docs build', [
        ('Ruff lint', 'ruff'), ('Ruff format', 'ruff-format'),
        ('Markdown Pages', 'snippets'), ('Notebook', 'notebooks'),
        ('Strict MkDocs build', 'mkdocs'),
    ]),
    ('previous-review', 'PR #8 | all five previous review regressions pass', [
        ('Original reviewer regression cases, unmodified', 'previous-review'),
    ]),
    ('additional-review', 'PR #8 | two new findings reproduced by three failing expectations', [
        ('Binary stdout / stderr; descendant process survives timeout', 'additional-review'),
    ]),
]
jobs = []
for slug, title, sections in groups:
    body = ''.join('<h2>' + html.escape(label) + '</h2><pre>' +
        html.escape((out / (name + '.txt')).read_text()) + '</pre>'
        for label, name in sections)
    document = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>' +
        html.escape(title) + '</title><style>' + style + '</style><h1>' +
        html.escape(title) + '</h1><p class="meta">Reviewed commit: ' + commit +
        '<br>Actual captured command output, shown in full. '
        'Source worktree remains unchanged. Each command and exit code is included.</p>' + body)
    (out / (slug + '.html')).write_text(document)
    jobs.append(slug)
(out / 'screenshot-jobs.json').write_text(json.dumps(jobs, indent=2) + '\n')
print('Built', len(jobs), 'local evidence pages')
