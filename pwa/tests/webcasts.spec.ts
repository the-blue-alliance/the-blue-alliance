import { expect, test } from '@playwright/test';

test('hydrates when the viewer is on a different date than the server', async ({
  page,
}) => {
  const pageErrors: Error[] = [];
  page.on('pageerror', (error) => pageErrors.push(error));
  // Every event is in the future for this viewer, but not for the server
  await page.clock.setFixedTime(new Date('2000-01-01T12:00:00Z'));

  await page.goto('/webcasts');
  await expect(page.locator('body[data-hydrated]')).toBeVisible();

  // Re-sorted by the viewer's date; early in a season nothing has a webcast
  const title = await page
    .getByRole('heading', { name: /Events with Webcasts/ })
    .textContent();
  const webcastCount = Number(title?.match(/(\d+) Events with Webcasts/)?.[1]);
  await expect(page.getByRole('heading', { name: 'Upcoming' })).toHaveCount(
    webcastCount > 0 ? 1 : 0,
  );
  await expect(page.getByRole('heading', { name: 'Past' })).toHaveCount(0);
  expect(pageErrors).toHaveLength(0);
});
