import { expect, test } from '@playwright/test';

test('districts table shows DCMP/CMP cutoff columns', async ({ page }) => {
  await page.goto('/districts/2024');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('columnheader', { name: 'DCMP Cutoff', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('columnheader', { name: 'CMP Cutoff', exact: true }),
  ).toBeVisible();

  const headers = page.getByRole('columnheader');
  await expect(headers).toHaveCount(7);

  const firstRowCells = page.getByRole('row').nth(1).getByRole('cell');
  await expect(firstRowCells).toHaveCount(7);
  await expect(firstRowCells.nth(4)).toHaveText(/^(\d+|-)$/);
  await expect(firstRowCells.nth(6)).toHaveText(/^(\d+|-)$/);
});

test('districts table shows skeletons while Teams/cutoff data loads', async ({
  page,
}) => {
  await page.route(
    /\/district\/[^/]+\/(advancement|teams\/keys)$/,
    async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    },
  );

  await page.goto('/districts/2024');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(page.locator('[data-slot="skeleton"]').first()).toBeVisible();

  await page.unrouteAll({ behavior: 'ignoreErrors' });

  await expect(page.locator('[data-slot="skeleton"]')).toHaveCount(0);

  const firstRowCells = page.getByRole('row').nth(1).getByRole('cell');
  await expect(firstRowCells.nth(2)).toHaveText(/^(\d+|-)$/);
  await expect(firstRowCells.nth(4)).toHaveText(/^(\d+|-)$/);
  await expect(firstRowCells.nth(6)).toHaveText(/^(\d+|-)$/);
});
