import { Page, expect, test } from '@playwright/test';

// The theme selector lives in the navbar profile menu as a
// light/dark/system radio group.
async function selectTheme(page: Page, name: 'Light' | 'Dark' | 'System') {
  await page.getByRole('button', { name: 'Account menu' }).click();
  await page.getByRole('menuitemradio', { name }).click();
  // Radio selection keeps the menu open; close it before interacting
  // with the page underneath
  await page.keyboard.press('Escape');
}

test.describe('Theme selection', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored preference before each test to start fresh
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('theme'));
    await page.reload();
    // Wait for React to finish hydrating so the menu is interactive
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('selecting Dark applies dark mode', async ({ page }) => {
    const html = page.locator('html');
    await selectTheme(page, 'Dark');
    await expect(html).toHaveClass(/dark/);
  });

  test('selecting Light switches back from dark mode', async ({ page }) => {
    const html = page.locator('html');
    await selectTheme(page, 'Dark');
    await expect(html).toHaveClass(/dark/);

    await selectTheme(page, 'Light');
    await expect(html).not.toHaveClass(/dark/);
  });

  test('theme persists across page reload', async ({ page }) => {
    const html = page.locator('html');
    await selectTheme(page, 'Dark');
    await expect(html).toHaveClass(/dark/);

    await page.reload();
    await expect(html).toHaveClass(/dark/);
  });

  test('theme persists after navigation', async ({ page }) => {
    const html = page.locator('html');
    await selectTheme(page, 'Dark');
    await expect(html).toHaveClass(/dark/);

    await page
      .locator('footer')
      .getByRole('link', { name: 'About us' })
      .click();
    await page.waitForURL('/about');
    await expect(html).toHaveClass(/dark/);
  });
});
