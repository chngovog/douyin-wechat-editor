const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error('Usage: node render_local_html_mobile.js <html> <png>');
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.BROWSER_EXE || undefined,
    args: ['--mute-audio'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 }, deviceScaleFactor: 1 });
    await page.route('**/*', route => {
      const protocol = new URL(route.request().url()).protocol;
      return ['file:', 'data:', 'about:'].includes(protocol) ? route.continue() : route.abort();
    });
    await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: 'load', timeout: 30000 });
    await page.evaluate(() => document.fonts.ready);
    const report = await page.evaluate(() => ({
      broken: Array.from(document.images).filter(i => !i.complete || !i.naturalWidth).length,
      overflow: document.documentElement.scrollWidth > window.innerWidth,
    }));
    if (report.broken || report.overflow) throw new Error(`Mobile layout failed: ${JSON.stringify(report)}`);
    await page.screenshot({ path: path.resolve(output), fullPage: true, timeout: 30000 });
    process.stdout.write('375px headless preview: no broken images or horizontal overflow\n');
  } finally {
    await browser.close();
  }
}
main().catch(error => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });
