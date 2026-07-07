import { expect, test } from '@playwright/test';

// Regression test for the Base UI Dialog migration: the match modal used
// Radix's onOpenAutoFocus to focus the dialog content container instead of
// the first tabbable element (which shows a focus ring and, in a tall
// modal, scrolls the popup to that element). The migration dropped it; the
// shared DialogContent now restores it via the focusContentOnOpen prop.

test('match modal focuses the dialog content container on open', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.waitForLoadState('networkidle');

  // Open the match modal via a match link (adds ?matchKey= search param)
  await page.getByRole('link', { name: 'Quals 1', exact: true }).click();

  const content = page.locator('[data-slot="dialog-content"]');
  await expect(content).toBeVisible();
  await expect(content).toBeFocused();
});
