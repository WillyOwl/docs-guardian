// Screenshot freshly captured logs and verify the actual built notebook in Chromium.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('/home/yiyang/F26project-DojoFoundations/node_modules/playwright-core');
const root = '/tmp/pr12-review-round3';
const output = path.join(root, 'artifacts');
const source = 'e1f15ea6789dc0d566c3c8d997a864419529fd83';
const site = path.join(root, 'escape-real/tinyml/site');
const origin = 'https://willyowl.github.io';
const prefix = '/docs-guardian/';
const esc = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/home/yiyang/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
    args: ['--no-sandbox'], headless: true,
  });
  if (!process.argv.includes('--logs-only')) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const responses = [];
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) return route.abort();
    if (!url.pathname.startsWith(prefix)) {
      responses.push({ url: url.href, status: 404, reason: 'outside published project path' });
      return route.fulfill({ status: 404, contentType: 'text/html', body: '<!doctype html><meta charset="utf-8"><style>body{font:24px sans-serif;margin:64px;line-height:1.6}code{background:#eee}</style><h1>404 — outside published site</h1><p>The clicked link resolved to <code>' + esc(url.href) + '</code>.</p><p>This replay publishes only the real MkDocs build under <code>/docs-guardian/</code>.</p><p>Source: <code>' + source + '</code>. Local publication replay; no live-site request.</p>' });
    }
    let local = path.join(site, decodeURIComponent(url.pathname.slice(prefix.length)));
    if (url.pathname.endsWith('/')) local = path.join(local, 'index.html');
    if (!local.startsWith(site + path.sep) || !fs.existsSync(local)) return route.fulfill({ status: 404, body: 'Missing built file' });
    const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.ico': 'image/x-icon' }[path.extname(local)] || 'application/octet-stream';
    await route.fulfill({ status: 200, contentType: mime, body: fs.readFileSync(local) });
  });
  await page.goto(origin + prefix + 'notebooks/walkthrough/', { waitUntil: 'networkidle' });
  const link = page.getByRole('link', { name: 'Review unpublished repository readme', exact: true });
  await link.scrollIntoViewIfNeeded();
  const href = await link.getAttribute('href');
  const resolved = await link.evaluate(a => a.href);
  assert.equal(href, '../../../../README.md');
  assert.equal(resolved, origin + '/README.md');
  await link.evaluate(a => { a.style.outline = '4px solid #c51b23'; a.style.background = '#fff1a8'; });
  await page.screenshot({ path: path.join(output, 'escape-notebook-rendered.png'), fullPage: false });
  await link.click();
  await page.waitForURL(origin + '/README.md');
  await page.getByRole('heading', { name: '404 — outside published site', exact: true }).waitFor();
  assert(responses.some(r => r.url === resolved && r.status === 404));
  await page.screenshot({ path: path.join(output, 'escape-browser-destination.png'), fullPage: true });
  fs.writeFileSync(path.join(output, 'browser-dom.txt'), [
    'PR #12 review round 3 — actual built notebook browser verification',
    'Source commit: ' + source,
    'Captured UTC: ' + new Date().toISOString(),
    '$ node /tmp/pr12-review-round3/render_screenshots.cjs',
    'Playwright replays actual built files at the configured publication origin.',
    'Requests inside /docs-guardian/ read only the generated build; other project-host paths return 404.',
    'This is a local publication replay, not a live deployment or a GitHub Pages response.',
    'Fixture: a notebook Markdown cell with [Review unpublished repository readme](../../../../README.md).',
    'Generated href: ' + href,
    'Browser resolved href: ' + resolved,
    'After click: ' + page.url(),
    'Observed response: ' + JSON.stringify(responses.find(r => r.url === resolved)),
    'PASS: the link escapes the published /docs-guardian/ path; the target is not in the build.',
    'Screenshots: escape-notebook-rendered.png, escape-browser-destination.png',
    '[exit 0]',
  ].join('\n') + '\n');
  await page.close();
  }

  const terminal = await browser.newPage({ viewport: { width: 1440, height: 200 }, deviceScaleFactor: 1 });
  const manifest = [];
  for (const name of fs.readdirSync(output).filter(n => n.endsWith('.txt')).sort()) {
    const raw = fs.readFileSync(path.join(output, name), 'utf8');
    const html = `<!doctype html><meta charset="utf-8"><title>${esc(name)}</title>
      <style>body{margin:0;background:#10151c;color:#e6edf3;font-family:monospace}header{padding:16px 22px;background:#1c2633;border-bottom:1px solid #445}h1{font-size:20px;margin:0 0 7px}.subtitle{font:13px sans-serif;color:#aab8c5}pre{margin:0;padding:20px 22px;font:14px/1.5 'DejaVu Sans Mono',monospace;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:4}</style>
      <header><h1>PR #12 · round 3 · ${esc(name.slice(0, -4))}</h1><div class="subtitle">Fresh captured command output · source e1f15ea · raw output and verification steps accompany this screenshot</div></header>
      <pre>${esc(raw)}</pre>`;
    fs.writeFileSync(path.join(output, name.replace(/\.txt$/, '.html')), html);
    await terminal.setContent(html);
    const file = name.replace(/\.txt$/, '.png');
    await terminal.screenshot({ path: path.join(output, file), fullPage: true });
    manifest.push({ log: name, screenshot: file });
  }
  fs.writeFileSync(path.join(output, 'screenshots.json'), JSON.stringify({ source, capturedUTC: new Date().toISOString(), commandOutput: manifest, builtPage: ['escape-notebook-rendered.png', 'escape-browser-destination.png'] }, null, 2) + '\n');
  await browser.close();
  console.log(`Captured ${manifest.length} command-output screenshots and 2 actual built-page screenshots.`);
})().catch(error => { console.error(error); process.exit(1); });
