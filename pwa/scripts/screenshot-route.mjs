#!/usr/bin/env node
// Screenshot a running dev-server route in light and dark mode, for the
// Before | After | Diff table in a PR description. See AGENTS.md "PR Screenshots".
//
//   node scripts/screenshot-route.mjs <url> <out-prefix> [selector]
//
// Writes <out-prefix>-light.png and <out-prefix>-dark.png. With a selector,
// captures just that element with the site navbar hidden so it never overlaps
// the capture; without one, captures the full page as a visitor sees it. The
// viewport is wide enough that the TanStack devtools badge stays clear of a
// centered `max-w-3xl` container. Works against any local server, not only
// the PWA (e.g. http://localhost:8080/ for a Jinja page).
import { chromium } from '@playwright/test';

const [url, prefix, selector] = process.argv.slice(2);
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
    // Let fonts and any entrance transitions settle.
    await page.waitForTimeout(800);
    const out = `${prefix}-${colorScheme}.png`;
    if (selector) {
      await page.addStyleTag({
        content: 'header, nav { display: none !important; }',
      });
      const el = page.locator(selector).first();
      await el.waitFor({ timeout: 30_000 });
      await el.scrollIntoViewIfNeeded();
      await el.screenshot({ path: out });
    } else {
      await page.screenshot({ path: out, fullPage: true });
    }
    console.log(`wrote ${out}`);
    await page.close();
  }
} finally {
  await browser.close();
}
