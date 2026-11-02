import { expect, test } from '@playwright/test';

test.describe('/suggest/match/video', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/suggest/match/video?match_key=2024mil_f1m2');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('links to the selected match', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Finals 2' })).toHaveAttribute(
      'href',
      '/match/2024mil_f1m2',
    );
  });

  test('links to the playlist form for the event', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Add them all at once' }),
    ).toHaveAttribute('href', '/suggest/event/video?event_key=2024mil');
  });

  test('shows the videos already on the match', async ({ page }) => {
    await expect(
      page.getByRole('heading', {
        name: /^Videos on The Blue Alliance \(\d+\)$/,
      }),
    ).toBeVisible();
  });

  test('prompts a signed-out user to sign in', async ({ page }) => {
    await page
      .getByRole('textbox', { name: 'YouTube URL' })
      .fill('https://www.youtube.com/watch?v=MQ0VNzIvHx0');
    await page.getByRole('button', { name: 'Add Video' }).click();

    await expect(
      page.getByRole('heading', { name: 'Sign in to suggest videos' }),
    ).toBeVisible();
  });
});
