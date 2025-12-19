import { expect, test } from '@playwright/test';

test.describe('Dark mode toggle', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test to start fresh
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('theme'));
    await page.reload();
    // Scroll to footer to make the toggle visible
    await page.locator('footer').scrollIntoViewIfNeeded();
  });

  test('toggle changes theme to dark mode', async ({ page }) => {
    // Initially should not have dark class (system default is usually light in tests)
    const html = page.locator('html');

    const toggleButton = page.getByRole('button', { name: 'Toggle Theme' });
    await toggleButton.click();

    // Verify dark class is applied
    await expect(html).toHaveClass(/dark/);
  });

  test('toggle changes theme to light mode', async ({ page }) => {
    const html = page.locator('html');
    const toggleButton = page.getByRole('button', { name: 'Toggle Theme' });

    // First set to dark
    await toggleButton.click();
    await expect(html).toHaveClass(/dark/);

    // Then switch to light
    await toggleButton.click();

    // Verify dark class is removed
    await expect(html).not.toHaveClass(/dark/);
  });

  test('theme persists across page reload', async ({ page }) => {
    const html = page.locator('html');
    const toggleButton = page.getByRole('button', { name: 'Toggle Theme' });

    // Set to dark mode
    await toggleButton.click();
    await expect(html).toHaveClass(/dark/);

    // Reload the page
    await page.reload();

    // Verify dark mode is still applied after reload
    await expect(html).toHaveClass(/dark/);
  });

  test('theme persists after navigation', async ({ page }) => {
    const html = page.locator('html');
    const toggleButton = page.getByRole('button', { name: 'Toggle Theme' });

    // Set to dark mode
    await toggleButton.click();
    await expect(html).toHaveClass(/dark/);

    // Navigate to another page using footer link
    await page
      .locator('footer')
      .getByRole('link', { name: 'About us' })
      .click();
    await page.waitForURL('/about');

    // Verify dark mode is still applied
    await expect(html).toHaveClass(/dark/);
  });
});
