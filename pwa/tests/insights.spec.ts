import { expect, test } from '@playwright/test';

test.describe('/insights/2026 leaderboards', () => {
  test('match leaderboards name the event and match rather than the key', async ({
    page,
  }) => {
    await page.goto('/insights/2026');
    await page.locator('body[data-hydrated]').waitFor();
    const link = page
      .locator('a[href^="/match/"]')
      .filter({ hasNot: page.locator('[data-slot="tooltip-content"]') })
      .first();
    await link.waitFor();
    const text = (await link.textContent())?.trim() ?? '';
    // e.g. "Archimedes Division Match 3", never "2026arc_sf3m1"
    expect(text).not.toMatch(/^\d{4}[a-z0-9]+_/);
    expect(text).toMatch(/Match \d+|Quals \d+|Finals \d+/);
    // The key is still available on hover
    await expect(link).toHaveAttribute('title', /^\d{4}[a-z0-9]+_/);
  });
});
