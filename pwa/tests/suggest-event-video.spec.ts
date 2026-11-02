import { expect, test } from '@playwright/test';

test.describe('/suggest/event/video', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/suggest/event/video?event_key=2024mil');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('links to the selected event', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: '2024 Milstein Division' }),
    ).toHaveAttribute('href', '/event/2024mil');
  });

  test('explains the match ID format', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Match IDs' }),
    ).toBeVisible();
  });

  test('prompts a signed-out user to sign in', async ({ page }) => {
    await page
      .getByRole('textbox', { name: 'YouTube playlist URL' })
      .fill(
        'https://www.youtube.com/playlist?list=PLLDODAGuIHqNRyZPxoHlvwMsJYP79ptCv',
      );
    await page.getByRole('button', { name: 'Load Playlist' }).click();

    await expect(
      page.getByRole('heading', { name: 'Sign in to suggest videos' }),
    ).toBeVisible();
  });
});
