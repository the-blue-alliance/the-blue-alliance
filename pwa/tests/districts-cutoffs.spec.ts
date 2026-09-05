import { expect, test } from '@playwright/test';

// The /districts table gained "DCMP Cutoff" / "CMP Cutoff" columns (minimum
// district points to advance) fed by a per-district getDistrictAdvancement query.
// Cutoff data may not exist for every district, so cells render "-" until (and
// unless) the advancement cutoffs are calculated.

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
