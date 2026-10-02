import { expect, test } from '@playwright/test';

test.describe('/suggest/event/media', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/suggest/event/media?event_key=2026necmp');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('shows the selected event', async ({ page }) => {
    await expect(page.getByText(/^2026 .*New England/).first()).toBeVisible();
  });

  test('advertises YouTube videos', async ({ page }) => {
    await expect(
      page.getByText('YouTube videos', { exact: true }),
    ).toBeVisible();
  });

  test('advertises SmugMug albums', async ({ page }) => {
    await expect(
      page.getByText('SmugMug albums', { exact: true }),
    ).toBeVisible();
  });

  test('shows existing event media', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /^Existing Media \(\d+\)$/ }),
    ).toBeVisible();
  });

  test('prompts a signed-out user to sign in', async ({ page }) => {
    await page
      .getByRole('textbox', { name: 'Media URL' })
      .fill('https://www.youtube.com/watch?v=pRaKQ0yCLJY');
    await page.getByRole('button', { name: 'Add Media' }).click();

    await expect(
      page.getByRole('heading', { name: 'Sign in to suggest media' }),
    ).toBeVisible();
  });
});
