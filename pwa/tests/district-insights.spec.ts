import { expect, test } from '@playwright/test';

test.describe('/district/fim/insights', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/district/fim/insights');
    await page.locator('body[data-hydrated]').waitFor();
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
  await page.goto('/district/fim/stats');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('heading', { name: 'Error 404 - Page Not Found' }),
  ).toBeVisible();
});
