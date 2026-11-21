import { expect, test } from '@playwright/test';

import { gotoHydrated } from './helpers';

test.describe('/events/regional/2025', () => {
  test.beforeEach(async ({ page }) => {
    await gotoHydrated(page, '/events/regional/2025');
  });

  test('shows how the top-ranked team qualified', async ({ page }) => {
    await expect(
      page.getByText('Engineering Inspiration Award at Pinnacles'),
    ).toBeVisible();
  });

  test('leaves low-ranked teams unrendered until filtered', async ({
    page,
  }) => {
    await expect(
      page.getByRole('link', { name: '9493', exact: true }),
    ).toHaveCount(0);
  });

  test('shows a low-ranked team when filtered by its number', async ({
    page,
  }) => {
    await page.getByLabel('Filter by team number').fill('9493');

    await expect(
      page.getByRole('link', { name: '9493', exact: true }),
    ).toBeVisible();
  });

  test('shows no results for an unknown team number', async ({ page }) => {
    await page.getByLabel('Filter by team number').fill('999999');

    await expect(page.getByText('No results.')).toBeVisible();
  });

  test('hides qualified teams when showing only unqualified teams', async ({
    page,
  }) => {
    await page.getByRole('button', { name: 'Not qualified' }).click();

    await expect(
      page.getByRole('link', { name: '4481', exact: true }),
    ).toHaveCount(0);
  });

  test('leaves pre-pool years out of the year selector', async ({ page }) => {
    await page.getByRole('button', { name: '2025' }).click();

    await expect(page.getByRole('menuitem', { name: '2024' })).toHaveCount(0);
  });
});

test('/events/regional stays on the regional rankings page', async ({
  page,
}) => {
  await gotoHydrated(page, '/events/regional');

  await expect(
    page.getByRole('heading', { name: /Regional Pool Rankings/ }),
  ).toBeVisible();
});

test('/events/regional/2024 shows the not found page', async ({ page }) => {
  await gotoHydrated(page, '/events/regional/2024');

  await expect(page.getByText('Error 404 - Page Not Found')).toBeVisible();
});
