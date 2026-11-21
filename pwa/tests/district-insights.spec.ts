import { expect, test } from '@playwright/test';

import { gotoHydrated } from './helpers';

test.describe('/district/fim/insights', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHydrated(page, '/district/fim/insights');
  });

  test('shows the all-time district insights heading', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'FIRST in Michigan Insights' }),
    ).toBeVisible();
  });

  test('shows event leaderboards from the former stats page', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Events' }).click();

    await expect(page.getByText('Most District Seasons')).toBeVisible();
  });
});

test('retired district stats URL is not found', async ({ page }) => {
  await gotoHydrated(page, '/district/fim/stats');

  await expect(
    page.getByRole('heading', { name: 'Error 404 - Page Not Found' }),
  ).toBeVisible();
});
