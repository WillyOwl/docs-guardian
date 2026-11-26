// Renders each check's terminal output (<name>.txt) to png/<name>.png.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('/home/yiyang/F26project-DojoFoundations/node_modules/playwright-core');

const EV = process.argv[2] || __dirname;
const NAMES = ['spec1-same-site-before-fix', 'spec1-same-site-fixed', 'spec2-notebook-anchor-before-fix', 'spec2-notebook-anchor-fixed', 'check-links-tests', 'links', 'markdownlint', 'vale', 'strict-build', 'pytest-3.14', 'pytest-3.11', 'ruff', 'ci'];

// Minimal ANSI SGR → HTML: bold, dim, and the 8 standard foreground colours.
const COLORS = { 30: '#555', 31: '#f14c4c', 32: '#23d18b', 33: '#e5e510', 34: '#3b8eea', 35: '#d670d6', 36: '#29b8db', 37: '#e5e5e5' };
function ansiToHtml(text) {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  let st = { bold: false, dim: false, color: null }, out = '';
  for (const part of text.split(/(\x1b\[[0-9;]*m)/)) {
    const m = part.match(/^\x1b\[([0-9;]*)m$/);
    if (!m) {
      if (!part) continue;
      const style = [st.bold && 'font-weight:bold', st.dim && 'opacity:.6', st.color && `color:${st.color}`].filter(Boolean).join(';');
      out += style ? `<span style="${style}">${esc(part)}</span>` : esc(part);
      continue;
    }
    for (const code of (m[1] || '0').split(';').map(Number)) {
      if (code === 0) st = { bold: false, dim: false, color: null };
      else if (code === 1) st.bold = true;
      else if (code === 2) st.dim = true;
      else if (code === 22) { st.bold = false; st.dim = false; }
      else if (code === 39) st.color = null;
      else if (COLORS[code]) st.color = COLORS[code];
    }
  }
  return out;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1100, height: 100 } });
  for (const name of NAMES) {
    const html = ansiToHtml(fs.readFileSync(path.join(EV, `${name}.txt`), 'utf8'));
    await page.setContent(`<body style="margin:0;background:#000;color:#e5e5e5">
      <pre style="margin:0;padding:8px;font:13px/1.25 'DejaVu Sans Mono',monospace;white-space:pre-wrap">${html}</pre></body>`);
    await page.screenshot({ path: path.join(EV, 'png', `${name}.png`), fullPage: true });
  }
  await browser.close();
  console.log(`rendered ${NAMES.length}`);
})().catch((e) => { console.error(e); process.exit(1); });
