import { expect, test } from '@playwright/test';

import { gotoHydrated } from './helpers';

test.describe('/request/apiwrite', () => {
  test('prompts a signed-out user to sign in', async ({ page }) => {
    await gotoHydrated(page, '/request/apiwrite');

    await expect(
      page.getByRole('heading', { name: 'Please log in to your TBA Account' }),
    ).toBeVisible();
  });
});
