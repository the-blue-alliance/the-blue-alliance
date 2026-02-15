/**
 * PWA Screenshot Capture Script
 *
 * Takes full-page screenshots of PWA pages using Playwright.
 * Pages to screenshot are specified via the PAGES env var (JSON array).
 * Designed to run against a built & running PWA server.
 *
 * Environment variables:
 *   BASE_URL       - Server URL (default: http://localhost:3000)
 *   SCREENSHOT_DIR - Output directory for screenshots (default: screenshots)
 *   PAGES          - JSON array of {name, path} objects for pages to screenshot
 */

import { mkdirSync } from "fs";
import { join } from "path";
import { pathToFileURL } from "url";

// Resolve @playwright/test from the working directory's node_modules (pwa/)
// rather than relative to this script's location (ops/pwa/).
// pnpm only hoists direct dependencies, so we use @playwright/test (direct dep)
// instead of playwright (transitive dep).
const pwPath = pathToFileURL(
  join(process.cwd(), "node_modules", "@playwright", "test", "index.mjs")
).href;
const { chromium } = await import(pwPath);

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const SCREENSHOT_DIR = process.env.SCREENSHOT_DIR || "screenshots";

// Pages to screenshot, specified via PAGES env var (JSON array of {name, path})
let PAGES = [];
if (process.env.PAGES) {
  try {
    PAGES = JSON.parse(process.env.PAGES);
    console.log(`Screenshotting ${PAGES.length} page(s) from PR description`);
  } catch (err) {
    console.warn(`Failed to parse PAGES: ${err.message}`);
  }
}

if (PAGES.length === 0) {
  console.log("No pages to screenshot. Add a ## Screenshot Pages section to the PR description.");
  process.exit(0);
}

function toFilename(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".png";
}

async function main() {
  mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
  });

  let captured = 0;
  let failed = 0;

  for (const page of PAGES) {
    const url = `${BASE_URL}${page.path}`;
    const filename = toFilename(page.name);
    const tab = await context.newPage();

    try {
      console.log(`Capturing ${page.name} (${url})...`);
      await tab.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
      // Brief extra wait for any client-side rendering to settle
      await tab.waitForTimeout(1000);
      await tab.screenshot({
        path: join(SCREENSHOT_DIR, filename),
        fullPage: true,
      });
      console.log(`  Saved ${filename}`);
      captured++;
    } catch (err) {
      console.warn(`  Failed to capture ${page.name}: ${err.message}`);
      failed++;
    }

    await tab.close();
  }

  await browser.close();

  console.log(
    `\nDone: ${captured} captured, ${failed} failed out of ${PAGES.length} pages`
  );

  if (captured === 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
