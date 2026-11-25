import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path('/home/yiyang/docs-guardian')
OUT = Path('/tmp/pr11-review-round2/39c7d29/round-2')
SHA = '39c7d290bbb0a982e8f173d518ea5b03fe23b84c'

def capture(name, commands, *, cwd=ROOT, env=None):
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == SHA
    lines = [f'PR #11 review round 2 | commit {SHA}',
             f'Captured UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}',
             f'Working directory: {cwd}', '']
    results = []
    for command in commands:
        lines.append('$ ' + shlex.join(command))
        started = time.monotonic()
        run = subprocess.run(command, cwd=cwd, env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines.extend([run.stdout.rstrip(), f'[exit {run.returncode}; {time.monotonic()-started:.2f}s]', ''])
        results.append(run.returncode)
    output = '\n'.join(lines)
    (OUT / f'{name}.txt').write_text(output + '\n')
    print(json.dumps({'check': name, 'exit_codes': results, 'log': str(OUT / f'{name}.txt')}), flush=True)
    return results

if __name__ == '__main__':
    py = '/tmp/pr11-review-round2/env314/bin/python'
    ruff = '/tmp/pr11-review-round2/env314/bin/ruff'
    cli = '/tmp/pr11-review-round2/env314/bin/docs-guardian'
    capture('pytest-3.14', [[py, '-m', 'pytest', '--color=no']])
    capture('ruff', [[ruff, 'check', '.'], [ruff, 'format', '--check', '.']])
    capture('snippets', [[cli, 'snippets', 'tinyml/docs']])
    capture('drift-current', [[cli, 'drift', '--base', 'origin/main', '--source', 'tinyml/src', '--docs', 'tinyml/docs']])
