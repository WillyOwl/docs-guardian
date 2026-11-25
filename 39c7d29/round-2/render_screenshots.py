"""Capture Chromium screenshots of the saved, unedited command outputs."""
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
CHROME = '/home/yiyang/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell'
STYLE = '''
body{margin:0;background:#101827;color:#e5e7eb;font-family:Arial,sans-serif}
main{margin:28px;padding:26px;background:#172135;border:1px solid #475569;border-radius:10px}
h1{font-size:23px;margin:0 0 12px}p{font-size:14px;color:#b7c8db;line-height:1.5}
pre{font:13px/20px "DejaVu Sans Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:24px}
article{background:white;color:#111827;padding:20px;border-radius:6px}
article p{color:#111827}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:12px;text-align:left}
code{font-family:monospace}a{color:#2866b8}
'''
manifest = []
def screenshot(name, body, height):
    source = HERE / f'{name}.html'
    source.write_text('<!doctype html><meta charset="utf-8"><style>' + STYLE + '</style>' + body)
    dest = HERE / f'{name}.png'
    run = subprocess.run([
        CHROME, '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
        '--hide-scrollbars', '--no-first-run', '--disable-background-networking',
        '--user-data-dir=/tmp/pr11-review-round2/chrome-profile',
        f'--window-size=1440,{height}', f'--screenshot={dest}', source.as_uri(),
    ], capture_output=True, text=True)
    if run.returncode or not dest.exists():
        raise RuntimeError(run.stderr)
    print(json.dumps({'screenshot': dest.name, 'bytes': dest.stat().st_size}), flush=True)
    manifest.append({'image': dest.name, 'source': source.name, 'viewport': [1440, height],
                     'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})

for path in sorted(HERE.glob('*.txt')):
    raw = path.read_text()
    display = re.sub(r'\x1b\[[0-9;]*m', '', raw)
    # The environmental failure is very long. Show the beginning and end, with
    # an explicit omission marker and the complete raw file retained alongside it.
    if path.stem == 'notebooks-sandbox':
        lines = display.splitlines()
        display = '\n'.join(lines[:25] + ['[Middle of traceback omitted from this view; complete output in notebooks-sandbox.txt]'] + lines[-12:])
    height = max(600, 275 + 20 * sum(max(1, math.ceil(len(line)/155)) for line in display.splitlines()))
    screenshot(path.stem, '<main><h1>PR #11 · Review round 2 · ' + html.escape(path.stem) +
               '</h1><p>Chromium capture of saved command output. Code under review: 39c7d290bbb0a982e8f173d518ea5b03fe23b84c.<br>' +
               'Raw output and reproduction steps are stored beside this screenshot.</p><pre>' + html.escape(display) + '</pre></main>', height)

response = (HERE / 'github-table-render.txt').read_text()
github_html = response[response.index('<'):response.rindex('[exit')].strip()
assert 'quickstart.md:2' not in github_html
report = (HERE / 'union-report.md').read_text()
screenshot('union-report-rendered',
    '<main><h1>PR #11 · Union signature report rendered by GitHub</h1>' +
    '<p>Actual response from GitHub POST /markdown (mode=gfm), captured in github-table-render.txt.<br>' +
    'Input has quickstart.md:2 in the Pages column. The rendered table loses it.</p>' +
    '<h2>Input from render_report at 39c7d29</h2><pre>' + html.escape(report) + '</pre>' +
    '<h2>GitHub-rendered output</h2><article>' + github_html + '</article></main>', 1050)
(HERE / 'screenshots.json').write_text(json.dumps(manifest, indent=2) + '\n')
