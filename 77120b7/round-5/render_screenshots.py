"""Capture complete saved output and the real GitHub-rendered report in Chromium."""
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
CHROME = '/home/yiyang/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell'
SHA = '77120b704a46df07b8fa18c418863523e26e9cd6'
STYLE = '''
body{margin:0;background:#101827;color:#e5e7eb;font-family:Arial,sans-serif}
main{margin:28px;padding:26px;background:#172135;border:1px solid #475569;border-radius:10px}
h1{font-size:23px;margin:0 0 12px}p{font-size:14px;color:#b7c8db;line-height:1.5}
pre{font:13px/20px "DejaVu Sans Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:24px}
article{background:white;color:#111827;padding:20px;border-radius:6px}
article p{color:#111827}table{border-collapse:collapse;width:100%}
th,td{border:1px solid #cbd5e1;padding:12px;text-align:left}code{font-family:monospace}
'''
manifest = []

def screenshot(name, body, height, source_log=None):
    source = HERE / f'{name}.html'
    source.write_text('<!doctype html><meta charset="utf-8"><style>' + STYLE + '</style>' + body)
    dest = HERE / f'{name}.png'
    result = subprocess.run([
        CHROME, '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
        '--hide-scrollbars', '--no-first-run', '--disable-background-networking',
        '--user-data-dir=/tmp/pr11-review-current/chrome-profile',
        f'--window-size=1440,{height}', f'--screenshot={dest}', source.as_uri(),
    ], capture_output=True, text=True)
    if result.returncode or not dest.exists():
        raise RuntimeError(result.stderr)
    entry = {'image': dest.name, 'source_html': source.name, 'viewport': [1440, height],
             'reviewed_commit': SHA, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
    if source_log:
        entry['source_log'] = source_log.name
        entry['source_log_sha256'] = hashlib.sha256(source_log.read_bytes()).hexdigest()
    manifest.append(entry)
    print(f'{dest.name}: {dest.stat().st_size} bytes', flush=True)

for path in sorted(HERE.glob('*.txt')):
    display = re.sub(r'\x1b\[[0-9;]*m', '', path.read_text())
    height = max(600, 275 + 20 * sum(max(1, math.ceil(len(line)/150)) for line in display.splitlines()))
    screenshot(path.stem,
               '<main><h1>PR #11 · Review round 5 · ' + html.escape(path.stem) + '</h1>' +
               '<p>Reviewed commit: ' + SHA + '.<br>' +
               'Chromium screenshot of the complete saved command output; original logs and commands are stored alongside.</p>' +
               '<pre>' + html.escape(display) + '</pre></main>', height, path)

(HERE / 'screenshots.json').write_text(json.dumps(manifest, indent=2) + '\n')
