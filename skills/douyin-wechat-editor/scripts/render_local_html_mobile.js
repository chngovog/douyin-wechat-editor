const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

async function main() {
  const args = process.argv.slice(2);
  const layoutOnly = args[0] === '--layout-check';
  if (layoutOnly) args.shift();
  const [input, output] = args;
  if (!input || !output) throw new Error('Usage: node render_local_html_mobile.js [--layout-check] <html> <png|json>');
  const digest = () => crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex');
  const htmlHash = digest();
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
    await page.evaluate(async () => {
      await Promise.all(Array.from(document.images, image => image.decode().catch(() => {})));
    });
    const report = await page.evaluate(() => ({
      viewport_width: window.innerWidth,
      broken_images: Array.from(document.images).filter(i => !i.complete || !i.naturalWidth).length,
      horizontal_overflow: document.documentElement.scrollWidth > window.innerWidth,
      page_height: document.documentElement.scrollHeight,
      images: Array.from(document.images, i => ({natural_width:i.naturalWidth, natural_height:i.naturalHeight,
        display_width:i.getBoundingClientRect().width, display_height:i.getBoundingClientRect().height})),
    }));
    Object.assign(report, {html_sha256:htmlHash, checked_at:new Date().toISOString(),
      passed:!report.broken_images && !report.horizontal_overflow && digest() === htmlHash,
      scope:'DOM layout only; no screenshot, semantic, visual or WeChat verification'});
    fs.mkdirSync(path.dirname(path.resolve(output)), {recursive:true});
    if (layoutOnly) fs.writeFileSync(output, JSON.stringify(report, null, 2));
    if (!report.passed) throw new Error(`Mobile layout failed: ${JSON.stringify(report)}`);
    if (!layoutOnly) await page.screenshot({ path: path.resolve(output), fullPage: true, timeout: 30000 });
    process.stdout.write(layoutOnly ? '375px layout checked without screenshot\n' : '375px legacy preview saved\n');
  } finally {
    await browser.close();
  }
}
main().catch(error => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });
