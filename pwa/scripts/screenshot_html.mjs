// Screenshot a saved HTML page (e.g. one rendered through the Flask test
// client) using the running dev server for its CSS/JS.
//
//   cd pwa && node scripts/screenshot_html.mjs <in.html> <out.png> [selector] [width]
//
// Lives in pwa/ because Node resolves `@playwright/test` from the script's own
// location, and only pwa/node_modules has it. The HTML should carry
// `<base href="http://localhost:8080/">` so relative asset URLs hit the dev
// server. With a selector, only that element's nearest `.container` (or the
// element itself, if none) is captured; without one, the full page is.
import { chromium } from '@playwright/test';
import { readFileSync } from 'fs';

const [, , input, output, selector, widthArg] = process.argv;
if (!input || !output) {
  console.error(
    'usage: screenshot_html.mjs <in.html> <out.png> [selector] [width]',
  );
  process.exit(2);
}
const width = Number(widthArg ?? 1180);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 900 } });
// Same origin as the <base href>, so relative asset requests resolve there.
await page.goto('http://localhost:8080/', { waitUntil: 'domcontentloaded' });
await page.setContent(readFileSync(input, 'utf8'), {
  waitUntil: 'networkidle',
});

if (selector) {
  const target = page.locator(selector).first();
  if ((await target.count()) === 0) {
    console.error(`selector matched nothing: ${selector}`);
    await browser.close();
    process.exit(1);
  }
  // Prefer the content container around the element; base.html's navbar is
  // also a .container, so never grab "the first .container" on the page.
  const container = target.locator(
    'xpath=ancestor::div[contains(@class,"container")][1]',
  );
  const box = await (
    (await container.count()) ? container : target
  ).boundingBox();
  await page.screenshot({
    path: output,
    clip: { ...box, height: Math.min(box.height, 1400) },
  });
} else {
  await page.screenshot({ path: output, fullPage: true });
}
await browser.close();
console.log(`wrote ${output}`);
