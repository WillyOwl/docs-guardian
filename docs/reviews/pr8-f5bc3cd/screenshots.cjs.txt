// Real screenshots of local HTML containing the complete recorded command output.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('/home/yiyang/F26project-DojoFoundations/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/home/yiyang/.cache/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-linux64/chrome-headless-shell',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
    const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, 'screenshot-jobs.json'), 'utf8'));
    for (const slug of jobs) {
      await page.goto('file://' + path.join(__dirname, slug + '.html'), { waitUntil: 'load' });
      await page.screenshot({ path: path.join(__dirname, slug + '.png'), fullPage: true });
      const size = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight }));
      console.log(`${slug}.png ${size.width}x${size.height}`);
    }
  } finally {
    await browser.close();
  }
})();
