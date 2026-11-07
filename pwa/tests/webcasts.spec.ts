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

  // Re-sorted by the viewer's date once hydrated
  await expect(page.getByRole('heading', { name: 'Upcoming' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Past' })).toHaveCount(0);
  expect(pageErrors).toHaveLength(0);
});
