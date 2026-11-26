#!/usr/bin/env python3
"""A minimized, deterministic contract loop: a valid site-root link must pass."""
import datetime
import os
from pathlib import Path
import subprocess
import sys

root = Path(os.environ.get('PR12_REVIEW_ROOT', '/tmp/pr12-review-round2'))
source = root / 'source'
site = root / 'minimal-root-relative'
(site / 'quickstart').mkdir(parents=True, exist_ok=True)
(site / 'index.html').write_text('<a href="/docs-guardian/quickstart/">Quickstart</a>\n')
(site / 'quickstart/index.html').write_text('<h1>Quickstart</h1>\n')
lychee = os.environ.get('LYCHEE_BIN', '/tmp/claude-1000/-home-yiyang-docs-guardian/ec08bf2d-2775-45e6-b9d0-9763870cb168/scratchpad/tools/bin/lychee-x86_64-unknown-linux-gnu/lychee')
lines = [
    'PR #12 review round 2 — minimal valid root-relative link',
    'Source commit: eab5b3ca743838c270066d5c3f72f9a13582832a',
    'Captured UTC: ' + datetime.datetime.now(datetime.timezone.utc).isoformat(),
    '$ python3 reproduce_root_relative.py',
    'Site fixture: index.html with one <a href="/docs-guardian/quickstart/">Quickstart</a>',
    'Destination: quickstart/index.html exists (served under /docs-guardian/ on GitHub Pages).',
    'Expected: exit 0, because the deployed link is valid.',
]
failures = 0
for attempt in range(1, 3):
    cmd = ['bash', str(source / '.github/scripts/check-links.sh'), str(site)]
    p = subprocess.run(cmd, cwd=source, env=os.environ | {'LYCHEE': lychee}, capture_output=True, text=True, timeout=10)
    lines += [f'Attempt {attempt}: ' + ' '.join(cmd), p.stdout.strip(), p.stderr.strip(), f'[exit {p.returncode}]']
    failures += p.returncode != 0
result = int(failures != 0)
lines += [f'FAIL: {failures}/2 attempts reject the valid root-relative link.' if result else 'PASS: valid root-relative link accepted in both attempts.', f'HARNESS EXIT: {result}']
output = '\n'.join(lines) + '\n'
(root / 'artifacts/root-relative-minimal.txt').write_text(output)
print(output, end='')
sys.exit(result)
