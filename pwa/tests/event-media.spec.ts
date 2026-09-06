import { expect, test } from '@playwright/test';

// 2026necmp is a completed event with a SmugMug photo gallery attached to the
// event itself (served by /event/{key}/media, not /team_media).
test('event Media tab renders SmugMug photo galleries', async ({ page }) => {
  await page.goto('/event/2026necmp');

  await page.getByRole('tab', { name: /Media/ }).click();

  const gallery = page.getByTestId('smugmug-album-gallery');
  await expect(gallery).toBeVisible();
  await expect(
    gallery.locator('a[href*="nefirst.smugmug.com"]').first(),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Photo Galleries' }),
  ).toBeVisible();
});
