// Render freshly captured check output and inspect the actual MkDocs mutation build.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_CORE_MODULE || '/home/yiyang/F26project-DojoFoundations/node_modules/playwright-core');
const root = process.env.PR12_REVIEW_ROOT || '/tmp/pr12-review-round2';
const output = path.join(root, 'artifacts');
const site = path.join(root, 'root-relative-actual/tinyml/site');
const origin = 'https://willyowl.github.io';
const prefix = '/docs-guardian/';
const esc = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_BIN || '/home/yiyang/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
    args: ['--no-sandbox'], headless: true,
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  // Replay built files at the deployment origin; no request reaches the live site.
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin || !url.pathname.startsWith(prefix)) return route.abort();
    let local = path.join(site, decodeURIComponent(url.pathname.slice(prefix.length)));
    if (url.pathname.endsWith('/')) local = path.join(local, 'index.html');
    if (!local.startsWith(site + path.sep) || !fs.existsSync(local)) return route.fulfill({ status: 404, body: 'Missing built file' });
    const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' }[path.extname(local)] || 'application/octet-stream';
    await route.fulfill({ status: 200, contentType: mime, body: fs.readFileSync(local) });
  });
  await page.goto(origin + prefix, { waitUntil: 'networkidle' });
  const link = page.getByRole('link', { name: 'Review valid root-relative quickstart', exact: true });
  await link.scrollIntoViewIfNeeded();
  const href = await link.getAttribute('href');
  if (href !== '/docs-guardian/quickstart/#quickstart') throw new Error('Fixture href missing');
  await page.screenshot({ path: path.join(output, 'root-relative-rendered.png'), fullPage: true });
  await link.click();
  await page.waitForURL(origin + prefix + 'quickstart/#quickstart');
  await page.locator('h1#quickstart').waitFor({ state: 'visible' });
  await page.screenshot({ path: path.join(output, 'root-relative-destination.png'), fullPage: true });
  fs.writeFileSync(path.join(output, 'browser-dom.txt'), [
    'PR #12 review round 2 — browser verification of root-relative link',
    'Source commit: eab5b3ca743838c270066d5c3f72f9a13582832a',
    'Captured UTC: ' + new Date().toISOString(),
    '$ node render_screenshots.cjs',
    'Playwright replays the actual mutation build at its configured site_url through request routing.',
    'All requests are fulfilled from local built files or aborted; this is not a live deployment screenshot.',
    'Link href: ' + href,
    'After clicking: ' + page.url(),
    'Destination h1#quickstart is visible: true',
    'PASS: the deployed-path link resolves to the existing Quickstart heading in a real browser.',
    'Browser page errors: ' + JSON.stringify(errors),
    'Screenshots: root-relative-rendered.png, root-relative-destination.png',
    '[exit 0]',
  ].join('\n') + '\n');
  await page.close();

  const terminal = await browser.newPage({ viewport: { width: 1440, height: 200 }, deviceScaleFactor: 1 });
  const manifest = [];
  function logs(dir) {
    return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
      const target = path.join(dir, entry.name);
      return entry.isDirectory() ? logs(target) : entry.name.endsWith('.txt') ? [path.relative(output, target)] : [];
    });
  }
  for (const name of logs(output).sort()) {
    const raw = fs.readFileSync(path.join(output, name), 'utf8');
    const html = `<!doctype html><meta charset="utf-8"><title>${esc(name)}</title>
      <style>body{margin:0;background:#10151c;color:#e6edf3;font-family:monospace}header{padding:16px 22px;background:#1c2633;border-bottom:1px solid #445}h1{font-size:20px;margin:0 0 7px}.subtitle{font:13px sans-serif;color:#aab8c5}pre{margin:0;padding:20px 22px;font:14px/1.5 'DejaVu Sans Mono',monospace;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:4}</style>
      <header><h1>PR #12 · round 2 · ${esc(name.slice(0, -4))}</h1><div class="subtitle">Fresh captured command output · source eab5b3c · raw logs and verification steps accompany this screenshot</div></header>
      <pre>${esc(raw)}</pre>`;
    fs.writeFileSync(path.join(output, name.replace(/\.txt$/, '.html')), html);
    await terminal.setContent(html);
    const file = name.replace(/\.txt$/, '.png');
    await terminal.screenshot({ path: path.join(output, file), fullPage: true });
    manifest.push({ log: name, screenshot: file });
  }
  fs.writeFileSync(path.join(output, 'screenshots.json'), JSON.stringify({ source: 'eab5b3ca743838c270066d5c3f72f9a13582832a', capturedUTC: new Date().toISOString(), commandOutput: manifest, builtPage: ['root-relative-rendered.png', 'root-relative-destination.png'] }, null, 2) + '\n');
  await browser.close();
  console.log(`Captured ${manifest.length} command-output screenshots and 2 actual built-page screenshots.`);
})().catch(error => { console.error(error); process.exit(1); });
