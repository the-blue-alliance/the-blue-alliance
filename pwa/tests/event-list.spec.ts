import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/events/2025');
});

test('championship divisions are listed under Einstein Field', async ({
  page,
}) => {
  const rows = page
    .locator('table')
    .filter({ hasText: 'Einstein Field' })
    .first()
    .locator('tbody tr');

  const keys = await rows.evaluateAll((els) =>
    els.map((el) => el.querySelector('a')?.getAttribute('href') ?? ''),
  );

  const einstein = keys.indexOf('/event/2025cmptx');
  const archimedes = keys.indexOf('/event/2025arc');

  expect(einstein).toBeGreaterThanOrEqual(0);
  expect(archimedes).toBe(einstein + 1);
});

test('division rows drop the parent event name prefix', async ({ page }) => {
  await expect(
    page.getByRole('link', { name: 'Mercury Division', exact: true }),
  ).toBeVisible();
});
