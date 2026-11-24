"""Record real commands against the clean, immutable PR worktree."""
import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

root = Path('/tmp/docs-guardian-pr8-round3')
out = Path(__file__).resolve().parent
name, *command = sys.argv[1:]
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
assert commit == '27b835360c9e8dc530f842b780ee14ccf73e9f26'
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True)
env = os.environ.copy()
env.update(NO_COLOR='1', PYTHONDONTWRITEBYTECODE='1', COLUMNS='110',
           JUPYTER_PLATFORM_DIRS='1', JUPYTER_RUNTIME_DIR=str(out / 'jupyter-runtime'),
           IPYTHONDIR=str(out / 'ipython'), NO_MKDOCS_2_WARNING='1')
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
begin = time.monotonic()
result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, timeout=120)
elapsed = time.monotonic() - begin
log = (f'PR #8 | commit {commit}\nUTC: {start}\nWorking tree: clean\nCWD: {root}\n'
       f'$ {shlex.join(command)}\n\n' + result.stdout +
       f'\n[exit {result.returncode}; {elapsed:.2f}s]\n')
(out / f'{name}.txt').write_text(log)
(out / f'{name}.json').write_text(json.dumps(dict(commit=commit, started=start,
    command=command, cwd=str(root), exit_code=result.returncode, elapsed=elapsed,
    clean=True), indent=2) + '\n')
print(log, end='')
sys.exit(result.returncode)
