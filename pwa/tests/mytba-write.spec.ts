import { expect, test } from '@playwright/test';

test.describe('Favorite button visibility', () => {
  test('Team page shows favorite button', async ({ page }) => {
    await page.goto('/team/604/2024');
    await expect(
      page.getByRole('button', { name: /add to favorites/i }),
    ).toBeVisible();
  });

  test('Event page shows favorite button', async ({ page }) => {
    await page.goto('/event/2024casj');
    await expect(
      page.getByRole('button', { name: /add to favorites/i }),
    ).toBeVisible();
  });
});

test.describe('Favorite button unauthenticated behavior', () => {
  test('Clicking favorite on team page opens login dialog', async ({
    page,
  }) => {
    await page.goto('/team/604/2024');
    await page.getByRole('button', { name: /add to favorites/i }).click();
    await expect(
      page.getByText('Sign in to use myTBA'),
    ).toBeVisible();
  });
});
