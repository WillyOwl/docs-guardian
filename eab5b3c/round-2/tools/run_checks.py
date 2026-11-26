#!/usr/bin/env python3
"""Capture PR #12 review checks on a pinned source; mutations live in scratch copies."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(os.environ.get('PR12_REVIEW_ROOT', '/tmp/pr12-review-round2'))
SOURCE = ROOT / 'source'
OUT = ROOT / 'artifacts'
SHA = 'eab5b3ca743838c270066d5c3f72f9a13582832a'
BASE = 'd48615c3386b813d0fc6845a23e1588e3c57bf67'
SCRATCH = Path('/tmp/claude-1000/-home-yiyang-docs-guardian/ec08bf2d-2775-45e6-b9d0-9763870cb168/scratchpad')
PYTHON = Path(os.environ.get('PR12_REVIEW_PYTHON', '/home/yiyang/docs-guardian/.venv/bin/python'))
PY311 = Path(os.environ.get('PR12_REVIEW_PY311', SCRATCH / 'env311/bin/python'))
LYCHEE = Path(os.environ.get('LYCHEE_BIN', SCRATCH / 'tools/bin/lychee-x86_64-unknown-linux-gnu/lychee'))
VALE = Path(os.environ.get('VALE_BIN', SCRATCH / 'tools/bin/vale'))
MDLINT = Path(os.environ.get('MARKDOWNLINT_BIN', '/home/yiyang/.npm/_npx/97a1abd67b237388/node_modules/.bin/markdownlint-cli2'))
CASE = sys.argv[1]
OUT.mkdir(parents=True, exist_ok=True)
LOG = (OUT / f'{CASE}.txt').open('w')
ENV = os.environ | {
    'NO_MKDOCS_2_WARNING': '1', 'PYTHONUNBUFFERED': '1',
    'PYTHONDONTWRITEBYTECODE': '1', 'LYCHEE': str(LYCHEE),
    'IPYTHONDIR': str(ROOT / 'ipython'),
}

def redact(value):
    value = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', str(value))
    for key, secret in os.environ.items():
        if re.search(r'(TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL)', key, re.I) and len(secret) > 8:
            value = value.replace(secret, '<REDACTED>')
    return value

def say(value):
    value = redact(value)
    print(value, flush=True)
    LOG.write(value + '\n')
    LOG.flush()

def run(argv, cwd=SOURCE, extra_env=None):
    argv = [str(x) for x in argv]
    env = ENV | {'PYTHONPATH': f'{cwd}/src:{cwd}/tinyml/src'} | (extra_env or {})
    say(f'$ (cd {cwd} && {shlex.join(argv)})')
    p = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, timeout=180)
    say(p.stdout.rstrip())
    say(f'[exit {p.returncode}]')
    return p.returncode, p.stdout

def copy_source(name):
    target = ROOT / name
    if target.exists():
        raise RuntimeError(f'Refusing to overwrite scratch copy {target}')
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns('.git', '.venv', '.cache', '__pycache__', 'site'))
    return target

def build(target=SOURCE):
    return run([PYTHON, '-m', 'mkdocs', 'build', '--strict', '-f', 'tinyml/mkdocs.yml'], target)

def links(target=SOURCE):
    return run(['bash', '.github/scripts/check-links.sh', 'tinyml/site'], target)

def tiny_site(name, markup):
    site = ROOT / 'fixtures' / name
    (site / 'quickstart').mkdir(parents=True, exist_ok=True)
    (site / 'index.html').write_text(f'<html><body><h1 id="home">Home</h1>{markup}</body></html>')
    (site / 'quickstart/index.html').write_text('<html><body><h1 id="install">Install</h1></body></html>')
    return run(['bash', SOURCE / '.github/scripts/check-links.sh', site])

say(f'PR #12 review round 2 — {CASE}')
say(f'Source commit: {SHA}')
say(f'Base commit: {BASE}')
say('Captured UTC: ' + datetime.datetime.now(datetime.timezone.utc).isoformat())
try:
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() == SHA
    if CASE == 'tool-versions':
        for argv in ([PYTHON, '--version'], [PY311, '--version'], [MDLINT, '--version'], [VALE, '--version'], [LYCHEE, '--version']):
            assert run(argv)[0] == 0
        for name, expected in [('vale_3.26.0_Linux_64-bit.tar.gz', '22aa69a556558e4a9dfc63c17030777383d8d3c48dcdfad655fa98e839d666ed'), ('lychee-x86_64-unknown-linux-gnu.tar.gz', '1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a')]:
            actual = hashlib.sha256((SCRATCH / 'tools/dl' / name).read_bytes()).hexdigest()
            say(f'{name} SHA-256: {actual}')
            assert actual == expected
        say('PASS: cached release archives match workflow SHA-256 pins.')
    elif CASE in ('pytest-314', 'pytest-311'):
        python = PYTHON if CASE == 'pytest-314' else PY311
        assert run([python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'])[0] == 0
    elif CASE == 'link-regressions':
        assert run([PYTHON, '-m', 'pytest', '-v', '-p', 'no:cacheprovider', 'tests/test_check_links.py'])[0] == 0
    elif CASE == 'markdownlint':
        assert run([MDLINT])[0] == 0
    elif CASE == 'vale':
        assert run([VALE, 'tinyml/docs'])[0] == 0
    elif CASE == 'strict-build':
        assert build()[0] == 0
    elif CASE == 'links':
        assert links()[0] == 0
    elif CASE == 'ruff':
        assert run([PYTHON, '-m', 'ruff', 'check', '.'])[0] == 0
        assert run([PYTHON, '-m', 'ruff', 'format', '--check', '.'])[0] == 0
    elif CASE == 'ci':
        code, output = run(['gh', 'pr', 'view', '12', '--repo', 'WillyOwl/docs-guardian', '--json', 'headRefOid,statusCheckRollup'])
        assert code == 0
        data = json.loads(output)
        assert data['headRefOid'] == SHA
        assert len(data['statusCheckRollup']) == 10
        assert all(item['conclusion'] == 'SUCCESS' for item in data['statusCheckRollup'])
        assert run(['gh', 'pr', 'checks', '12', '--repo', 'WillyOwl/docs-guardian'])[0] == 0
        say('PASS: all 10 CI checks succeed on the pinned latest head.')
    elif CASE in ('same-site-fixed', 'notebook-anchor-fixed'):
        target = copy_source(CASE)
        if CASE == 'same-site-fixed':
            page = target / 'tinyml/docs/index.md'
            original = page.read_text()
            page.write_text(original + '\n[Review missing page](https://willyowl.github.io/docs-guardian/pr12-review-missing-page/)\n')
            needle = 'pr12-review-missing-page'
        else:
            page = target / 'tinyml/docs/notebooks/walkthrough.ipynb'
            notebook = json.loads(page.read_text())
            notebook['cells'].append({'cell_type': 'markdown', 'id': 'review-round2', 'metadata': {}, 'source': ['[Review missing heading](#pr12-review-missing-heading)\n']})
            page.write_text(json.dumps(notebook, indent=1) + '\n')
            needle = 'pr12-review-missing-heading'
        assert run(['diff', '-u', SOURCE / page.relative_to(target), page], target)[0] == 1
        assert build(target)[0] == 0
        code, output = links(target)
        assert code == 2 and needle in output
        say('PASS: strict-build succeeds; real link Gate rejects the original round-1 symptom (exit 2).')
    elif CASE == 'boundary-probes':
        cases = [
            ('valid-relative', '<a href="quickstart/#install">Install</a>', 0),
            ('missing-relative', '<a href="missing/">Missing</a>', 2),
            ('valid-same-site', '<a href="https://willyowl.github.io/docs-guardian/quickstart/#install">Install</a>', 0),
            ('missing-same-site', '<a href="https://willyowl.github.io/docs-guardian/missing/">Missing</a>', 2),
            ('valid-heading', '<a href="#home">Home</a>', 0),
            ('missing-heading', '<a href="#missing">Missing</a>', 2),
            ('valid-root-relative', '<a href="/docs-guardian/quickstart/#install">Install</a>', 0),
        ]
        failures = []
        for name, markup, expected in cases:
            say(f'CASE {name}; expected exit {expected}; HTML {markup}')
            code, output = tiny_site(name, markup)
            if code != expected:
                failures.append(name)
        say('Contract failures: ' + json.dumps(failures))
        assert not failures
    elif CASE == 'root-relative-actual':
        target = copy_source(CASE)
        page = target / 'tinyml/docs/index.md'
        page.write_text(page.read_text() + '\n[Review valid root-relative quickstart](/docs-guardian/quickstart/#quickstart)\n')
        assert run(['diff', '-u', SOURCE / page.relative_to(target), page], target)[0] == 1
        assert build(target)[0] == 0
        html = (target / 'tinyml/site/index.html').read_text()
        assert 'href="/docs-guardian/quickstart/#quickstart"' in html
        assert 'id="quickstart"' in (target / 'tinyml/site/quickstart/index.html').read_text()
        say('PASS: generated href is root-relative, and its local destination and heading exist.')
        code, output = links(target)
        assert code == 2 and 'provide a root dir' in output
        say('CONFIRMED P2: the real strict build passes but the links Gate rejects this valid deployed URL.')
    elif CASE == 'root-relative-controls':
        site = ROOT / 'minimal-root-relative'
        mount = ROOT / 'control-web-root'
        mount.mkdir(exist_ok=True)
        if not (mount / 'docs-guardian').exists():
            (mount / 'docs-guardian').symlink_to(site, target_is_directory=True)
        cmd = [LYCHEE, '--config', SOURCE / 'lychee.toml', '--remap', rf'^https://willyowl\.github\.io/docs-guardian/ file://{site}/']
        say('Ranked predictions recorded before controls:')
        say('1. Missing site-root context: adding --root-dir with the deployed /docs-guardian/ mount makes the same valid link pass.')
        say('2. Directory index resolution: a root context alone will still fail unless the href explicitly names index.html.')
        say('3. HTTPS remap interference: root context alone will still fail unless the remap is removed.')
        assert run([*cmd, site])[0] == 2
        assert run([*cmd, '--root-dir', mount, site])[0] == 0
        say('PASS: changing only --root-dir turns red to green, without changing the remap, href or index_files.')
        say('Supported cause: missing site-root context. Hypotheses 2 and 3 falsified.')
        original = (site / 'index.html').read_text()
        (site / 'index.html').write_text('<a href="/docs-guardian/missing/">Missing</a>\n')
        code, output = run([*cmd, '--root-dir', mount, site])
        assert code == 2 and 'missing' in output
        (site / 'index.html').write_text(original)
        say('PASS: a missing destination still fails with the same root context. This is a diagnosis control, not a committed fix.')
    elif CASE == 'integrity':
        assert run(['git', 'rev-parse', 'HEAD'])[1].strip() == SHA
        assert run(['git', 'diff', '--exit-code', 'HEAD'])[0] == 0
        code, output = run(['git', 'status', '--short', '--untracked-files=normal'])
        assert code == 0 and not output.strip()
        assert run(['git', 'diff', '--check', BASE + '...HEAD'])[0] == 0
        say('PASS: tracked source is unchanged and worktree is clean.')
    else:
        raise ValueError(CASE)
except Exception as error:
    say(f'FAIL: {type(error).__name__}: {error}')
    say('HARNESS EXIT: 1')
    raise SystemExit(1)
say('HARNESS EXIT: 0')
