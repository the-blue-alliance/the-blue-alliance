import { expect, test } from '@playwright/test';

test.describe('/events/2025', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/events/2025');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('lists championship divisions immediately after Einstein Field', async ({
    page,
  }) => {
    const einsteinRow = page
      .locator('table')
      .filter({ hasText: 'Einstein Field' })
      .first()
      .getByRole('row')
      .filter({
        has: page.getByRole('link', { name: 'Einstein Field', exact: true }),
      });

    await expect(
      einsteinRow.locator('xpath=following-sibling::tr[1]'),
    ).toContainText('Archimedes Division');
  });

  test('drops the parent event name from division rows', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Mercury Division', exact: true }),
    ).toBeVisible();
  });
});

test.describe('/events', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/events');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('labels the district selector as All Events', async ({ page }) => {
    await expect(
      page.getByRole('combobox').filter({ hasText: 'All Events' }),
    ).toBeVisible();
  });
});
