import { expect, test } from '@playwright/test';

test.describe('/suggest/team/social_media', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/suggest/team/social_media?team_key=frc1124');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('shows the selected team', async ({ page }) => {
    await expect(page.getByText(/^Team 1124 — /)).toBeVisible();
  });

  test('advertises GitHub accounts', async ({ page }) => {
    await expect(
      page.getByText('GitHub accounts', { exact: true }),
    ).toBeVisible();
  });

  test('shows the existing social media heading', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Existing social media accounts' }),
    ).toBeVisible();
  });

  test('prompts a signed-out user to sign in', async ({ page }) => {
    await page
      .getByRole('textbox', { name: 'Social media URL' })
      .fill('https://github.com/frc1124');
    await page.getByRole('button', { name: 'Add Social Media' }).click();

    await expect(
      page.getByRole('heading', { name: 'Sign in to suggest social media' }),
    ).toBeVisible();
  });
});
