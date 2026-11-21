import { expect, test } from '@playwright/test';

import { gotoHydrated } from './helpers';

test.describe('/teams/2', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHydrated(page, '/teams/2');
  });

  test('labels the selected page by team number range', async ({ page }) => {
    await expect(page.getByRole('combobox')).toContainText('1000s');
  });

  test('does not use the raw page number as the selector label', async ({
    page,
  }) => {
    await expect(page.getByRole('combobox')).not.toHaveText(/^2$/);
  });
});

test.describe('/teams', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHydrated(page, '/teams');
  });

  test('labels the first page by team number range', async ({ page }) => {
    await expect(page.getByRole('combobox')).toContainText('1-999');
  });

  test('shows multiple page ranges when the selector opens', async ({
    page,
  }) => {
    await page.getByRole('combobox').click();

    await expect(
      page.getByRole('listbox').getByRole('option').nth(3),
    ).toBeInViewport();
  });
});
