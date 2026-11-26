#!/usr/bin/env python3
"""Capture actual PR checks and deterministic mutation probes; never edit source."""
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

ROOT = Path(os.environ.get('PR12_REVIEW_ROOT', '/tmp/pr12-review'))
SOURCE = ROOT / 'source'
OUT = ROOT / 'e7db35c' / 'round-1'
PYTHON = Path(os.environ.get('PR12_REVIEW_PYTHON', '/home/yiyang/docs-guardian/.venv/bin/python'))
TOOLS = Path('/tmp/claude-1000/-home-yiyang-docs-guardian/ec08bf2d-2775-45e6-b9d0-9763870cb168/scratchpad/tools/bin')
VALE = Path(os.environ.get('VALE_BIN', TOOLS / 'vale'))
LYCHEE = Path(os.environ.get('LYCHEE_BIN', TOOLS / 'lychee-x86_64-unknown-linux-gnu' / 'lychee'))
MDLINT = Path(os.environ.get('MARKDOWNLINT_BIN', '/home/yiyang/.npm/_npx/97a1abd67b237388/node_modules/.bin/markdownlint-cli2'))
OUT.mkdir(parents=True, exist_ok=True)
CASE = sys.argv[1]
LOG = OUT / f'{CASE}.txt'
STREAM = LOG.open('w')
ENV = os.environ.copy()
ENV.update(NO_MKDOCS_2_WARNING='1', PYTHONUNBUFFERED='1', IPYTHONDIR=str(ROOT / 'ipython'), PYTHONDONTWRITEBYTECODE='1')

def say(message):
    print(message, flush=True)
    STREAM.write(str(message) + '\n')
    STREAM.flush()

def redact(value):
    value = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', value)
    for key, secret in os.environ.items():
        if re.search(r'(TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL)', key, re.I) and len(secret) > 8:
            value = value.replace(secret, '<REDACTED>')
    return value

def run(argv, cwd=SOURCE):
    argv = [str(arg) for arg in argv]
    env = ENV | {'PYTHONPATH': f'{cwd}/src:{cwd}/tinyml/src'}
    say(f'$ (cd {cwd} && {shlex.join(argv)})')
    proc = subprocess.run(argv, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    say(redact(proc.stdout).rstrip())
    say(f'[exit {proc.returncode}]')
    return proc.returncode, proc.stdout

def scratch():
    target = ROOT / CASE
    if target.exists():
        raise RuntimeError(f'Refusing to reuse mutation directory: {target}')
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns('.git', '.venv', '.cache', '__pycache__', 'site'))
    return target

def build(cwd):
    return run([PYTHON, '-m', 'mkdocs', 'build', '--strict', '-f', 'tinyml/mkdocs.yml'], cwd)

def links(cwd, *extra):
    return run([LYCHEE, *extra, 'tinyml/site'], cwd)

say('PR #12 independent review — ' + CASE)
say('Source commit: e7db35cdf9cd8c70e63dc592d821f9243875dc76')
say('Base commit: d48615c3386b813d0fc6845a23e1588e3c57bf67')
say('Captured UTC: ' + datetime.datetime.now(datetime.timezone.utc).isoformat())

if CASE == 'tool-versions':
    statuses = [run([PYTHON, '--version'])[0], run([MDLINT, '--version'])[0], run([VALE, '--version'])[0], run([LYCHEE, '--version'])[0]]
    for tool in (VALE, LYCHEE):
        say(f'Binary SHA-256 {tool.name}: {hashlib.sha256(tool.read_bytes()).hexdigest()}')
    result = max(statuses)
elif CASE == 'markdownlint':
    result = run([MDLINT])[0]
elif CASE == 'vale':
    result = run([VALE, 'tinyml/docs'])[0]
elif CASE == 'strict-build':
    result = build(SOURCE)[0]
elif CASE == 'links':
    result = links(SOURCE)[0]
elif CASE == 'pytest':
    result = run([PYTHON, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'])[0]
elif CASE == 'ruff':
    result = max(run([PYTHON, '-m', 'ruff', 'check', '.'])[0], run([PYTHON, '-m', 'ruff', 'format', '--check', '.'])[0])
elif CASE == 'ci':
    code, output = run(['gh', 'pr', 'view', '12', '--repo', 'WillyOwl/docs-guardian', '--json', 'headRefOid,statusCheckRollup'])
    data = json.loads(output)
    assert code == 0 and data['headRefOid'] == 'e7db35cdf9cd8c70e63dc592d821f9243875dc76'
    assert len(data['statusCheckRollup']) == 10
    assert all(check['conclusion'] == 'SUCCESS' for check in data['statusCheckRollup'])
    result = run(['gh', 'pr', 'checks', '12', '--repo', 'WillyOwl/docs-guardian'])[0]
    say('PASS: all 10 CI checks are successful on the reviewed head SHA.')
elif CASE == 'source-integrity':
    code, output = run(['git', 'rev-parse', 'HEAD'])
    assert code == 0 and output.strip() == 'e7db35cdf9cd8c70e63dc592d821f9243875dc76'
    assert run(['git', 'diff', '--exit-code', 'HEAD'])[0] == 0
    code, output = run(['git', 'status', '--short', '--untracked-files=normal'])
    assert code == 0 and not output.strip()
    result = run(['git', 'diff', '--check', 'd48615c3386b813d0fc6845a23e1588e3c57bf67...HEAD'])[0]
    say('PASS: baseline worktree remains clean at the reviewed source commit.')
elif CASE in ('notebook-anchor', 'same-site-url', 'notebook-anchor-online', 'same-site-url-online', 'notebook-anchor-minimal'):
    target = scratch()
    if CASE.startswith('notebook-anchor'):
        page = target / 'tinyml/docs/notebooks/walkthrough.ipynb'
        notebook = json.loads(page.read_text())
        cell = {'cell_type': 'markdown', 'id': 'pr12-missing-anchor', 'metadata': {}, 'source': ['[Review missing heading](#pr12-review-missing-heading)\n']}
        if CASE == 'notebook-anchor-minimal':
            notebook['cells'] = [cell]
        else:
            notebook['cells'].append(cell)
        page.write_text(json.dumps(notebook, indent=1) + '\n')
        say('Mutation: append one Markdown cell: ' + cell['source'][0].strip())
    else:
        page = target / 'tinyml/docs/index.md'
        mutation = '\n[Review missing page](https://willyowl.github.io/docs-guardian/pr12-review-missing-page/)\n'
        page.write_text(page.read_text() + mutation)
        say('Mutation: append one Markdown link: ' + mutation.strip())
    say('Original SHA-256: ' + hashlib.sha256((SOURCE / page.relative_to(target)).read_bytes()).hexdigest())
    say('Mutated SHA-256:  ' + hashlib.sha256(page.read_bytes()).hexdigest())
    run(['diff', '-u', SOURCE / page.relative_to(target), page], target)
    build_code, _ = build(target)
    link_code, _ = links(target, *([] if CASE.endswith('-online') else ['--offline']))
    result = int(build_code == 0 and link_code == 0)
    say('ASSERT: at least one Gate rejects the broken internal destination.')
    say('FAIL: strict-build and links both accept the planted error.' if result else 'PASS: a Gate rejected the planted error.')
elif CASE == 'anchor-controls':
    from html.parser import HTMLParser
    class Anchors(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()
            self.links = set()
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if 'id' in attrs:
                self.ids.add(attrs['id'])
            if tag == 'a' and 'href' in attrs:
                self.links.add(attrs['href'])
    target = ROOT / 'notebook-anchor'
    parser = Anchors()
    parser.feed((target / 'tinyml/site/notebooks/walkthrough/index.html').read_text())
    assert '#pr12-review-missing-heading' in parser.links
    assert 'pr12-review-missing-heading' not in parser.ids
    say('PASS: generated notebook HTML contains the planted href and lacks its target id.')
    original_code, _ = links(target, '--offline')
    fragment_code, fragment_output = links(target, '--offline', '--include-fragments=anchor-only')
    assert original_code == 0
    assert fragment_code != 0 and 'pr12-review-missing-heading' in fragment_output
    say('PASS: changing only fragment validation makes the identical generated site fail.')
    fixed = scratch()
    page = fixed / 'tinyml/docs/notebooks/walkthrough.ipynb'
    notebook = json.loads(page.read_text())
    notebook['cells'].append({'cell_type': 'markdown', 'id': 'pr12-anchor-control', 'metadata': {}, 'source': ['## Review valid heading\n', '\n', '[Review valid heading](#review-valid-heading)\n']})
    page.write_text(json.dumps(notebook, indent=1) + '\n')
    assert build(fixed)[0] == 0
    assert links(fixed, '--offline', '--include-fragments=anchor-only')[0] == 0
    say('PASS: valid notebook anchor passes the same fragment-enabled check.')
    markdown = fixed / 'tinyml/docs/index.md'
    markdown.write_text(markdown.read_text() + '\n[Review missing heading](#pr12-review-missing-heading)\n')
    code, output = build(fixed)
    assert code != 0 and 'pr12-review-missing-heading' in output
    say('PASS: same invalid fragment in Markdown is rejected by strict-build.')
    result = 0
elif CASE == 'same-site-controls':
    target = ROOT / 'same-site-url'
    html = (target / 'tinyml/site/index.html').read_text()
    assert 'https://willyowl.github.io/docs-guardian/pr12-review-missing-page/' in html
    assert not (target / 'tinyml/site/pr12-review-missing-page/index.html').exists()
    say('PASS: generated HTML contains the planted URL; its local destination is absent.')
    remap = f'https://willyowl.github.io/docs-guardian/(.*) file://{target}/tinyml/site/$1'
    code, output = links(target, '--offline', '--remap', remap)
    assert code != 0 and 'pr12-review-missing-page' in output
    say('PASS: remapping the same URL to the local build makes lychee reject it.')
    fixed = scratch()
    page = fixed / 'tinyml/docs/index.md'
    page.write_text(page.read_text() + '\n[Review missing page](pr12-review-missing-page/)\n')
    build(fixed)
    code, output = links(fixed, '--offline')
    assert code != 0 and 'pr12-review-missing-page' in output
    say('PASS: relative form of the same nonexistent destination fails lychee.')
    result = 0
else:
    raise SystemExit('Unknown case: ' + CASE)

say('HARNESS EXIT: ' + str(result))
STREAM.close()
raise SystemExit(result)
