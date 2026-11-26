#!/usr/bin/env python3
"""Capture fresh checks against the pinned PR head; no source fixes are applied."""
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

ROOT = Path('/tmp/pr12-review-round3')
SOURCE = ROOT / 'source'
OUT = ROOT / 'artifacts'
SHA = 'e1f15ea6789dc0d566c3c8d997a864419529fd83'
BASE = 'd48615c3386b813d0fc6845a23e1588e3c57bf67'
SCRATCH = Path('/tmp/claude-1000/-home-yiyang-docs-guardian/ec08bf2d-2775-45e6-b9d0-9763870cb168/scratchpad')
PYTHON = Path('/home/yiyang/docs-guardian/.venv/bin/python')
PY311 = SCRATCH / 'env311/bin/python'
LYCHEE = SCRATCH / 'tools/bin/lychee-x86_64-unknown-linux-gnu/lychee'
VALE = SCRATCH / 'tools/bin/vale'
MDLINT = Path('/home/yiyang/.npm/_npx/97a1abd67b237388/node_modules/.bin/markdownlint-cli2')
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

say(f'PR #12 review round 3 — {CASE}')
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
    elif CASE == 'live-destination':
        url = 'https://willyowl.github.io/README.md'
        code, output = run(['curl', '--silent', '--show-error', '--location', '--max-time', '20', '--output', '/dev/null', '--write-out', 'HTTP %{http_code}\nFinal URL: %{url_effective}\n', url])
        assert code == 0 and 'HTTP 404' in output
        say('PASS: the current public target of the notebook link independently returns HTTP 404.')
    elif CASE == 'ruff':
        assert run([PYTHON, '-m', 'ruff', 'check', '.', '--no-cache'])[0] == 0
        assert run([PYTHON, '-m', 'ruff', 'format', '--check', '.', '--no-cache'])[0] == 0
    elif CASE == 'snippets':
        assert run([PYTHON, '-m', 'docs_guardian.cli', 'snippets', 'tinyml/docs'])[0] == 0
    elif CASE == 'notebooks':
        assert run([PYTHON, '-m', 'pytest', '--nbmake', 'tinyml/docs/notebooks', '-q', '-p', 'no:cacheprovider'])[0] == 0
    elif CASE == 'ci':
        code, output = run(['gh', 'pr', 'view', '12', '--repo', 'WillyOwl/docs-guardian', '--json', 'headRefOid,statusCheckRollup'])
        assert code == 0
        data = json.loads(output)
        assert data['headRefOid'] == SHA
        assert len(data['statusCheckRollup']) == 10
        assert all(item['conclusion'] == 'SUCCESS' for item in data['statusCheckRollup'])
        assert run(['gh', 'pr', 'checks', '12', '--repo', 'WillyOwl/docs-guardian'])[0] == 0
        say('PASS: all 10 CI checks succeed on the pinned latest head.')
    elif CASE == 'boundary-probes':
        cases = [
            ('valid-relative', 'quickstart/#install', 0),
            ('missing-relative', 'missing/', 2),
            ('valid-same-site', 'https://willyowl.github.io/docs-guardian/quickstart/#install', 0),
            ('missing-same-site', 'https://willyowl.github.io/docs-guardian/missing/', 2),
            ('missing-same-site-heading', 'https://willyowl.github.io/docs-guardian/quickstart/#missing', 2),
            ('valid-heading', '#home', 0),
            ('missing-heading', '#missing', 2),
            ('valid-root-relative', '/docs-guardian/quickstart/#install', 0),
            ('valid-site-root', '/docs-guardian/', 0),
            ('missing-root-relative', '/docs-guardian/missing/', 2),
            ('missing-root-relative-heading', '/docs-guardian/quickstart/#missing', 2),
            ('unprefixed-root-relative', '/quickstart/', 2),
        ]
        for name, href, expected in cases:
            site = ROOT / 'fixtures' / name
            (site / 'quickstart').mkdir(parents=True, exist_ok=True)
            (site / 'index.html').write_text(f'<html><body><h1 id="home">Home</h1><a href="{href}">Test</a></body></html>')
            (site / 'quickstart/index.html').write_text('<html><body><h1 id="install">Install</h1></body></html>')
            say(f'CASE {name}; expected exit {expected}; href={href}')
            code, output = run(['bash', SOURCE / '.github/scripts/check-links.sh', site])
            assert code == expected, name
        say(f'PASS: all {len(cases)} valid/broken URL and anchor contracts hold using the actual script.')
    elif CASE == 'original-repros':
        target = copy_source('original-repros')
        page = target / 'tinyml/docs/index.md'
        original = page.read_text()
        page.write_text(original + '\n[Review valid root-relative quickstart](/docs-guardian/quickstart/#quickstart)\n')
        assert build(target)[0] == 0
        assert links(target)[0] == 0
        say('PASS: original round-2 valid root-relative link is accepted in the real build.')
        patch = subprocess.run(['diff', '-u', '--label', 'a/tinyml/docs/index.md', '--label', 'b/tinyml/docs/index.md', str(SOURCE / 'tinyml/docs/index.md'), str(page)], text=True, capture_output=True)
        assert patch.returncode == 1
        (OUT / 'root-relative-valid.patch').write_text(patch.stdout)
        page.write_text(original + '\n[Review missing same-site page](https://willyowl.github.io/docs-guardian/pr12-review-missing-page/)\n')
        assert build(target)[0] == 0
        code, output = links(target)
        assert code == 2 and 'pr12-review-missing-page' in output
        say('PASS: original round-1 broken same-site URL is rejected in the real build.')
        page.write_text(original)
        notebook_path = target / 'tinyml/docs/notebooks/walkthrough.ipynb'
        notebook = json.loads(notebook_path.read_text())
        notebook['cells'].append({'cell_type': 'markdown', 'id': 'review-round3', 'metadata': {}, 'source': ['[Review missing heading](#pr12-review-missing-heading)\n']})
        notebook_path.write_text(json.dumps(notebook, indent=1) + '\n')
        assert build(target)[0] == 0
        code, output = links(target)
        assert code == 2 and 'pr12-review-missing-heading' in output
        say('PASS: original round-1 broken notebook heading link is rejected in the real build.')
    elif CASE == '404-coverage':
        site = ROOT / '404-fixture'
        shutil.copytree(SOURCE / 'tinyml/site', site)
        page = site / '404.html'
        original = page.read_text()
        page.write_text(original + '<a href="/docs-guardian/review-missing-404/">Review missing 404 destination</a>')
        code, output = run(['bash', SOURCE / '.github/scripts/check-links.sh', site])
        assert code == 2 and 'review-missing-404' in output
        say('PASS: a broken link added only to the built 404.html is rejected (exit 2).')
    elif CASE == 'escape-minimal':
        root = ROOT / 'escape-minimal'
        site = root / 'site'
        site.mkdir(parents=True, exist_ok=True)
        (site / 'index.html').write_text('<a href="../unpublished.html">Unpublished</a>')
        (root / 'unpublished.html').write_text('<h1>Unpublished checkout file</h1>')
        say('Published site has only index.html. The destination exists outside that site.')
        say('Expected: reject ../unpublished.html, which is /unpublished.html on the deployed host.')
        code, output = run(['bash', SOURCE / '.github/scripts/check-links.sh', site])
        assert code != 0, 'FALSE NEGATIVE: the Gate accepts a link to an unpublished checkout file.'
    elif CASE == 'escape-real':
        target = copy_source('escape-real')
        notebook_path = target / 'tinyml/docs/notebooks/walkthrough.ipynb'
        notebook = json.loads(notebook_path.read_text())
        notebook['cells'].append({'cell_type': 'markdown', 'id': 'review-escape', 'metadata': {}, 'source': ['[Review unpublished repository readme](../../../../README.md)\n']})
        notebook_path.write_text(json.dumps(notebook, indent=1) + '\n')
        assert build(target)[0] == 0
        html = target / 'tinyml/site/notebooks/walkthrough/index.html'
        assert 'href="../../../../README.md"' in html.read_text()
        local_target = (html.parent / '../../../../README.md').resolve()
        assert local_target == target / 'README.md' and local_target.is_file()
        say('Generated href: ../../../../README.md')
        say('Local resolved target: ' + str(local_target))
        say('Deployed browser URL resolves to https://willyowl.github.io/README.md, outside published /docs-guardian/.')
        code, output = links(target)
        assert code != 0, 'FALSE NEGATIVE: strict build and link Gate both accept a link outside the deployed site.'
    elif CASE == 'escape-controls':
        root = ROOT / 'escape-minimal'
        site = root / 'site'
        outside = root / 'unpublished.html'
        original = outside.read_text()
        cmd = ['bash', SOURCE / '.github/scripts/check-links.sh', site]
        say('Ranked predictions announced before controls:')
        say('1. Host filesystem resolution: removing only the unpublished outside file changes acceptance to rejection.')
        say('2. Same-site remap interference: removing only --remap changes acceptance to rejection.')
        say('3. Ignored/excluded link: detailed output reports skipped/excluded instead of OK.')
        for attempt in range(1, 4):
            say(f'Repeat {attempt}: outside destination exists; bug must repeat.')
            code, output = run(cmd)
            assert code == 0 and '1 OK' in output
        outside.unlink()
        try:
            code, output = run(cmd)
            assert code == 2 and 'unpublished.html' in output and 'File not found' in output
        finally:
            outside.write_text(original)
        say('PASS: changing only existence of the unpublished file changes accepted to rejected; relative traversal confirmed.')
        mount = ROOT / 'escape-web-root'
        mount.mkdir(exist_ok=True)
        if not (mount / 'docs-guardian').exists():
            (mount / 'docs-guardian').symlink_to(site, target_is_directory=True)
        code, output = run([LYCHEE, '--config', SOURCE / 'lychee.toml', '--root-dir', mount, '--verbose', site])
        assert code == 0 and '1 OK' in output
        say('PASS: no --remap still accepts the outside file; hypothesis 2 falsified. The output counts 1 OK, not excluded; hypothesis 3 falsified.')
        isolated = ROOT / 'escape-isolated/site'
        shutil.copytree(site, isolated)
        code, output = run(['bash', SOURCE / '.github/scripts/check-links.sh', isolated])
        assert code == 2 and 'unpublished.html' in output
        say('PASS: copying only published files into an isolated directory rejects the same href. This is a diagnosis control, not a source fix.')
    elif CASE == 'lint-controls':
        target = copy_source('lint-controls')
        page = target / 'tinyml/docs/index.md'
        original = page.read_text()
        page.write_text(original + '\n# Duplicate h1\n')
        code, output = run([MDLINT], target)
        assert code != 0 and 'MD025' in output
        say('PASS: Markdown structure mutation is caught by markdownlint (MD025).')
        page.write_text(original + '\nGithub hosts this project.\n')
        code, output = run([VALE, 'tinyml/docs'], target)
        assert code != 0 and 'GitHub' in output
        say('PASS: product name mutation is caught by the Vale house style.')
    elif CASE == 'strict-controls':
        target = copy_source('strict-controls')
        page = target / 'tinyml/docs/index.md'
        original = page.read_text()
        page.write_text(original + '\n[Missing heading](quickstart.md#review-missing-heading)\n')
        code, output = build(target)
        assert code != 0 and 'review-missing-heading' in output
        say('PASS: a broken Markdown cross-reference/heading fails strict build.')
        page.write_text(original)
        (target / 'tinyml/docs/review-unlisted.md').write_text('# Unlisted Page\n')
        code, output = build(target)
        assert code != 0 and 'review-unlisted.md' in output
        say('PASS: a Page missing from nav fails strict build.')
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
