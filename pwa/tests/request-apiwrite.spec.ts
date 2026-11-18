import { expect, test } from '@playwright/test';

test.describe('/request/apiwrite', () => {
  test('prompts a signed-out user to sign in', async ({ page }) => {
    await page.goto('/request/apiwrite');
    await page.locator('body[data-hydrated]').waitFor();

    await expect(
      page.getByRole('heading', { name: 'Please log in to your TBA Account' }),
    ).toBeVisible();
  });
});
