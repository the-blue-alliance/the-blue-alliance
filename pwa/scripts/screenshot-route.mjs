#!/usr/bin/env node
// Screenshot one element of a running dev-server route in light and dark mode,
// for before/after tables in PR descriptions. See AGENTS.md "PR Screenshots".
//
//   node scripts/screenshot-route.mjs <url> <out-prefix> [selector]
//
// Writes <out-prefix>-light.png and <out-prefix>-dark.png of `selector`
// (default `#shot`) with the site navbar hidden so it never overlaps the
// capture. The viewport is wide enough that the TanStack devtools badge
// stays clear of a centered `max-w-3xl` container.
import { chromium } from '@playwright/test';

const [url, prefix, selector = '#shot'] = process.argv.slice(2);
if (!url || !prefix) {
  console.error(
    'usage: node scripts/screenshot-route.mjs <url> <out-prefix> [selector]',
  );
  process.exit(2);
}

const browser = await chromium.launch();
try {
  for (const colorScheme of ['light', 'dark']) {
    const page = await browser.newPage({
      viewport: { width: 1200, height: 1000 },
      colorScheme,
    });
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60_000 });
    await page.addStyleTag({
      content: 'header, nav { display: none !important; }',
    });
    const el = page.locator(selector).first();
    await el.waitFor({ timeout: 30_000 });
    await el.scrollIntoViewIfNeeded();
    // Let fonts and any entrance transitions settle.
    await page.waitForTimeout(800);
    const out = `${prefix}-${colorScheme}.png`;
    await el.screenshot({ path: out });
    console.log(`wrote ${out}`);
    await page.close();
  }
} finally {
  await browser.close();
}
