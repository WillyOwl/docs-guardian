// Screenshots of captured command output and the actual rendered mutation page.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('/home/yiyang/F26project-DojoFoundations/node_modules/playwright-core');
const root = '/tmp/pr12-review';
const output = path.join(root, 'e7db35c', 'round-1');
const esc = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/home/yiyang/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
    args: ['--no-sandbox'],
    headless: true,
  });
  const site = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  await site.route(/^https?:/, route => route.abort());
  await site.goto('file://' + root + '/notebook-anchor-minimal/tinyml/site/notebooks/walkthrough/index.html');
  const link = site.getByRole('link', { name: 'Review missing heading', exact: true });
  await link.scrollIntoViewIfNeeded();
  const state = await site.evaluate(() => ({
    href: document.querySelector('a[href="#pr12-review-missing-heading"]')?.getAttribute('href'),
    targetExists: Boolean(document.getElementById('pr12-review-missing-heading')),
  }));
  if (state.href !== '#pr12-review-missing-heading' || state.targetExists) throw new Error('Mutation DOM assertion failed');
  await site.screenshot({ path: path.join(output, 'notebook-rendered.png'), fullPage: true });
  fs.writeFileSync(path.join(output, 'browser-dom.txt'), [
    'PR #12 independent review — browser DOM verification',
    'Source commit: e7db35cdf9cd8c70e63dc592d821f9243875dc76',
    'Captured UTC: ' + new Date().toISOString(),
    'Mutation: notebook reduced to one Markdown cell containing one missing-heading link.',
    '$ node render_screenshots.cjs',
    'Playwright opens the built notebook HTML, locates the visible link, and queries its target id.',
    JSON.stringify(state, null, 2),
    'PASS: the link is rendered and visible; the target heading does not exist.',
    'Screenshot: notebook-rendered.png (actual rendered mutation site).',
    '[exit 0]',
  ].join('\n') + '\n');
  await site.close();

  const page = await browser.newPage({ viewport: { width: 1440, height: 200 }, deviceScaleFactor: 1 });
  for (const name of fs.readdirSync(output).filter(f => f.endsWith('.txt')).sort()) {
    const raw = fs.readFileSync(path.join(output, name), 'utf8');
    const html = `<!doctype html><meta charset="utf-8"><title>${esc(name)}</title>
      <style>body{margin:0;background:#10151c;color:#e6edf3;font-family:monospace}header{padding:16px 22px;background:#1c2633;border-bottom:1px solid #445}h1{font-size:20px;margin:0 0 7px}.subtitle{font:13px sans-serif;color:#aab8c5}pre{margin:0;padding:20px 22px;font:14px/1.5 'DejaVu Sans Mono',monospace;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:4}</style>
      <header><h1>PR #12 · ${esc(name.slice(0, -4))}</h1><div class="subtitle">Captured command output · source e7db35c · logs and reproduction steps accompany this screenshot</div></header>
      <pre>${esc(raw)}</pre>`;
    fs.writeFileSync(path.join(output, name.replace(/\.txt$/, '.html')), html);
    await page.setContent(html);
    await page.screenshot({ path: path.join(output, name.replace(/\.txt$/, '.png')), fullPage: true });
  }
  await browser.close();
  process.stdout.write('Saved command-output screenshots and notebook-rendered.png.\n');
})().catch(error => { console.error(error); process.exit(1); });
