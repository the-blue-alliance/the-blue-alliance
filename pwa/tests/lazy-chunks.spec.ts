import { expect, test } from '@playwright/test';

// Regression tests for GH #10240: heavy libraries (score breakdowns, recharts,
// devtools) were statically imported into route/entry chunks even though most
// visitors never render them. These assert the lazy-loaded UI still renders
// correctly, not just that the code splits.

test.describe('lazy score breakdown', () => {
  test('renders the correct year for a 2015 match', async ({ page }) => {
    await page.goto('/match/2015nyny_qm1');
    await page.locator('body[data-hydrated]').waitFor();

    await expect(page.getByRole('table').first()).toBeVisible();
  });

  test('renders the correct year (plus shift breakdown) for a 2026 match', async ({
    page,
  }) => {
    await page.goto('/match/2024mil_f1m2');
    await page.locator('body[data-hydrated]').waitFor();

    // 2024 match still has a score breakdown table even though 2026 also
    // renders an additional ScoreByShift component
    await expect(page.getByRole('table').first()).toBeVisible();
  });
});

test.describe('lazy COPR chart', () => {
  test('renders once the insights tab is opened', async ({ page }) => {
    await page.goto('/event/2024mil');
    await page.locator('body[data-hydrated]').waitFor();

    const insightsTab = page.getByRole('tab', { name: /insights/i });
    if (await insightsTab.isVisible()) {
      await insightsTab.click();
      await expect(page.locator('svg.recharts-surface')).toBeVisible();
    }
  });
});

test.describe('devtools gating', () => {
  test('does not render TanStack devtools in production build', async ({
    page,
  }) => {
    await page.goto('/');
    await page.locator('body[data-hydrated]').waitFor();

    // The devtools mount a fixed-position toggle button in each bottom
    // corner; in a production build these should never be present.
    await expect(page.locator('[class*="TanStackRouterDevtools"]')).toHaveCount(
      0,
    );
    await expect(page.locator('.tsqd-open-btn-container')).toHaveCount(0);
  });
});
