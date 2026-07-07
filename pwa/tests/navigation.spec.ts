import { expect, test } from '@playwright/test';

// Regression tests for the Base UI NavigationMenu migration:
// - Base UI derives open state from `value != null`, so controlling the
//   menu with '' as the closed sentinel left the root permanently "open"
//   and the popup portal permanently mounted
// - Base UI opens triggers on hover by default (no opt-out prop); the
//   mobile hamburger must stay click-only

const viewport = { width: 500, height: 800 };

test('nav popup portal is not mounted while the menu is closed', async ({
  page,
}) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await expect(
    page.locator('[data-slot="navigation-menu-viewport"]'),
  ).toHaveCount(0);
});

test.describe('hamburger menu (narrow viewport)', () => {
  test.use({ viewport });

  test('does not open on hover', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const trigger = page.getByRole('button', { name: 'Toggle Menu' });
    await trigger.hover();
    // Base UI's hover-open delay is 50ms; give it ample time to misfire
    await page.waitForTimeout(400);

    await expect(
      page.locator('[data-slot="navigation-menu-viewport"]'),
    ).toHaveCount(0);
  });

  test('opens on click and fully unmounts on second click', async ({
    page,
  }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const trigger = page.getByRole('button', { name: 'Toggle Menu' });
    await trigger.click();
    // The viewport wrapper itself is zero-height (the mobile menu content
    // is absolutely positioned), so assert on a menu item inside the portal
    const viewport = page.locator('[data-slot="navigation-menu-viewport"]');
    await expect(viewport).toHaveCount(1);
    await expect(viewport.getByRole('link').first()).toBeVisible();

    await trigger.click();
    // With '' as the controlled value the root never reached the closed
    // state, so the portal stayed mounted forever
    await expect(
      page.locator('[data-slot="navigation-menu-viewport"]'),
    ).toHaveCount(0);
  });
});
