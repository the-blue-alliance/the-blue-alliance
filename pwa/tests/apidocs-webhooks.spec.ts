import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/apidocs/webhooks');
  await expect(page.locator('body[data-hydrated]')).toBeVisible();
});

test('scrolls to Alliance Selection when its table of contents link is clicked', async ({
  page,
}) => {
  await page.getByRole('link', { name: 'Alliance Selection' }).first().click();

  await expect(
    page.getByRole('heading', { name: 'Alliance Selection' }),
  ).toBeInViewport();
});

test('shows the verification message example', async ({ page }) => {
  await expect(
    page.getByText(
      '"verification_key": "8279a61abdeee0cf46a86136bf888188a4b18cdf"',
    ),
  ).toBeVisible();
});

test('asks signed-out users to sign in before sending a test notification', async ({
  page,
}) => {
  await expect(
    page.getByRole('link', { name: 'Sign in' }).first(),
  ).toHaveAttribute('href', '/account');
});
