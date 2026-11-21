import type { Page } from '@playwright/test';

export async function gotoHydrated(page: Page, url: string) {
  await page.goto(url);
  await page.locator('body[data-hydrated]').waitFor();
}

export async function hangRequests(page: Page, url: RegExp) {
  await page.route(url, () => new Promise(() => {}));
}

export async function delayRequests(page: Page, url: RegExp, ms: number) {
  await page.route(url, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, ms));
    await route.continue();
  });
}

export function recordRequests(page: Page, urlPart = ''): string[] {
  const urls: string[] = [];
  page.on('request', (request) => {
    if (request.url().includes(urlPart)) {
      urls.push(request.url());
    }
  });
  return urls;
}
