import { expect, test } from '@playwright/test';

test.describe('/districts/2024', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/districts/2024');
    await page.locator('body[data-hydrated]').waitFor();
  });

  ['DCMP Cutoff', 'CMP Cutoff'].forEach((name) => {
    test(`shows the ${name} column`, async ({ page }) => {
      await expect(
        page.getByRole('columnheader', { name, exact: true }),
      ).toBeVisible();
    });
  });

  test('shows six district table columns', async ({ page }) => {
    await expect(page.getByRole('columnheader')).toHaveCount(6);
  });

  test('shows six values in each district row', async ({ page }) => {
    await expect(page.getByRole('row').nth(1).getByRole('cell')).toHaveCount(6);
  });

  (
    [
      ['team count', 1],
      ['DCMP cutoff', 3],
      ['CMP cutoff', 5],
    ] as const
  ).forEach(([name, index]) => {
    test(`shows the ${name} for each district`, async ({ page }) => {
      await expect(
        page.getByRole('row').nth(1).getByRole('cell').nth(index),
      ).toHaveText(/^(\d+|-)$/);
    });
  });
});

test('shows placeholders while district details load', async ({ page }) => {
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
});
