import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/faq');
  await expect(page.locator('body[data-hydrated]')).toBeVisible();
});

test('scrolls to Feature Requests when its table of contents link is clicked', async ({
  page,
}) => {
  await page.getByRole('link', { name: 'Feature Requests' }).click();

  await expect(
    page.getByRole('heading', { name: 'Feature Requests' }),
  ).toBeInViewport();
});

test('links the Team Admin Dashboard to /mod', async ({ page }) => {
  await expect(
    page.getByRole('link', { name: 'Team Admin Dashboard' }).first(),
  ).toHaveAttribute('href', '/mod');
});
