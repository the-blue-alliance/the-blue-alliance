import { expect, test } from '@playwright/test';

test('event page fetches Nexus from the browser, not the SSR loader', async ({
  page,
}) => {
  const nexusRequests: string[] = [];
  page.on('request', (r) => {
    if (r.url().includes('/nexus_info')) nexusRequests.push(r.url());
  });

  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await expect.poll(() => nexusRequests.length).toBeGreaterThan(0);
});

test('past-year district championship page stops polling', async ({ page }) => {
  await page.clock.install();

  const eventsRequests: string[] = [];
  page.on('request', (r) => {
    if (r.url().includes('/api/v3/events/2019')) eventsRequests.push(r.url());
  });

  await page.goto('/district/fim/champs/2019');
  await page.locator('body[data-hydrated]').waitFor();
  await expect.poll(() => eventsRequests.length).toBeGreaterThan(0);

  const afterLoad = eventsRequests.length;
  await page.clock.fastForward('03:00');
  await page.waitForTimeout(500);

  expect(eventsRequests.length).toBe(afterLoad);
});
