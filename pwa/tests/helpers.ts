import type { Page } from '@playwright/test';

export async function gotoHydrated(page: Page, url: string) {
  await page.goto(url);
  await page.locator('body[data-hydrated]').waitFor();
}
