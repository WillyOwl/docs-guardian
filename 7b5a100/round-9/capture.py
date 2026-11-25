"""Run checks against the reviewed checkout and retain complete command output."""
import datetime
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path('/tmp/pr11-review-round9/source')
OUT = Path(__file__).resolve().parent
SHA = '7b5a100481ec7a078551d307325c3f422f48793b'
PY314 = '/tmp/pr11-review-round2/env314/bin/python'
PY311 = '/tmp/pr11-review-round2/env311/bin/python'
PYDOCS = '/tmp/pr11-review-round2/envdocs/bin/python'

def capture(name, commands, cwd=ROOT):
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == SHA
    env = {**os.environ, 'PYTHONPATH': f'{ROOT}/src:{ROOT}/tinyml/src',
           'PYTHONDONTWRITEBYTECODE': '1', 'IPYTHONDIR': '/tmp/pr11-review-round9/ipython',
           'MKDOCS_JUPYTER_CACHE_DIR': '/tmp/pr11-review-round9/mkdocs-cache', 'JUPYTER_RUNTIME_DIR': '/tmp/pr11-review-round9/jupyter', 'NO_COLOR': '1'}
    lines = [f'PR #11 review round 9 | reviewed commit {SHA}',
             f'Captured UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}',
             f'Working directory: {cwd}',
             f'PYTHONPATH={env["PYTHONPATH"]}', '']
    codes = []
    for command in commands:
        lines.append('$ ' + shlex.join(command))
        started = time.monotonic()
        run = subprocess.run(command, cwd=cwd, env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines.extend([run.stdout.rstrip(), f'[exit {run.returncode}; {time.monotonic()-started:.2f}s]', ''])
        codes.append(run.returncode)
    (OUT / f'{name}.txt').write_text('\n'.join(lines) + '\n')
    print(f'{name}: exit codes {codes}; log {OUT / (name + ".txt")}', flush=True)
    return codes

if __name__ == '__main__':
    name = sys.argv[1]
    tasks = {
        'head-provenance': [['git', 'rev-parse', 'HEAD'], ['git', 'status', '--porcelain'],
                            ['git', 'diff', '--check'],
                            ['git', 'ls-remote', 'origin', 'refs/heads/feat/drift-check', 'refs/pull/11/head'],
                            ['gh', 'pr', 'view', '11', '--repo', 'WillyOwl/docs-guardian', '--json', 'headRefOid,state,isDraft']],
        'pytest-3.14': [[PY314, '--version'], [PY314, '-m', 'pytest', '-p', 'no:cacheprovider', '--color=no']],
        'pytest-3.11': [[PY311, '--version'], [PY311, '-m', 'pytest', '-p', 'no:cacheprovider', '--color=no']],
        'ruff': [[PY314, '-m', 'ruff', 'check', '.'], [PY314, '-m', 'ruff', 'format', '--check', '.']],
        'snippets': [[PY314, '-c', 'from docs_guardian.cli import main; raise SystemExit(main())', 'snippets', 'tinyml/docs']],
        'drift-current': [[PY314, '-c', 'from docs_guardian.cli import main; raise SystemExit(main())', 'drift', '--base', 'origin/main', '--source', 'tinyml/src', '--docs', 'tinyml/docs']],
        'notebooks': [[PYDOCS, '-m', 'pytest', '--nbmake', 'tinyml/docs/notebooks', '-p', 'no:cacheprovider', '--color=no']],
        'build-docs': [[PYDOCS, '-m', 'mkdocs', 'build', '--strict', '-f', 'tinyml/mkdocs.yml', '-d', '/tmp/pr11-review-round9/site']],
        'review-probes-3.11': [[PY311, '-m', 'pytest', str(OUT / 'test_review_round9.py'), '-vv', '--tb=short', '-p', 'no:cacheprovider', '--color=no']],
        'review-probes': [[PYDOCS, '-m', 'pytest', str(OUT / 'test_review_round9.py'), '-vv', '--tb=short', '-p', 'no:cacheprovider', '--color=no']],
        'finding-reproductions': [[PYDOCS, str(OUT / 'reproduce_findings.py')]],
        'github-render': [['gh', 'api', '--method', 'POST', 'markdown', '-f', 'mode=gfm', '-F', f'text=@{OUT}/report-demo.md']],
        'ci': [['gh', 'pr', 'checks', '11', '--repo', 'WillyOwl/docs-guardian'],
               ['gh', 'pr', 'view', '11', '--repo', 'WillyOwl/docs-guardian', '--json', 'headRefOid,state,isDraft']],
        'environment': [[PY314, '-c', "import sys, docs_guardian.drift, tinyml; from importlib.metadata import version; print(sys.version); print('drift source:', docs_guardian.drift.__file__); print('tinyml source:', tinyml.__file__); print({n:version(n) for n in ['pytest','ruff','markdown-it-py','numpy']})"],
                        [PY311, '-c', "import sys; from importlib.metadata import version; print(sys.version); print({n:version(n) for n in ['pytest','markdown-it-py','numpy']})"],
                        [PYDOCS, '-c', "import sys; from importlib.metadata import version; print(sys.version); print({n:version(n) for n in ['nbmake','mkdocs','mkdocs-material','markdown-it-py']})"],
                        ['git', 'rev-parse', 'HEAD'], ['git', 'status', '--porcelain'], ['git', 'diff', '--check']],
    }
    codes = capture(name, tasks[name])
    raise SystemExit(any(code != 0 for code in codes))
