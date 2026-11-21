import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/brand');
  await expect(page.locator('body[data-hydrated]')).toBeVisible();
});

[
  ['Download blue logo as SVG', '/images/brand/logo-blue.svg'],
  ['Download blue logo as PNG', '/images/brand/logo-blue.png'],
  ['Download blue logo as AI', '/images/brand/logo-blue.ai'],
  ['Download white logo as SVG', '/images/brand/logo-white.svg'],
  ['Download white logo as PNG', '/images/brand/logo-white.png'],
  ['Download white logo as AI', '/images/brand/logo-white.ai'],
].forEach(([name, expectedHref]) => {
  test(`links "${name}" to ${expectedHref}`, async ({ page }) => {
    await expect(page.getByRole('link', { name })).toHaveAttribute(
      'href',
      expectedHref,
    );
  });
});

test('serves the blue logo download', async ({ request }) => {
  const response = await request.get('/images/brand/logo-blue.svg');

  expect(response.ok()).toBe(true);
});
