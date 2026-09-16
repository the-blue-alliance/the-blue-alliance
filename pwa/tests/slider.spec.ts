import { expect, test } from '@playwright/test';

// Regression test for the Base UI Slider migration: DoubleSlider spread the
// Radix-named minStepsBetweenThumbs prop onto Base UI's Slider.Root, which
// doesn't recognize it, so it leaked into the DOM as an attribute (and any
// nonzero value would be silently ignored — Base UI's prop is
// minStepsBetweenValues).

test('team stats year slider does not leak unknown props to the DOM', async ({
  page,
}) => {
  await page.goto('/team/254/stats');
  await page.waitForLoadState('networkidle');

  // The slider renders (two thumbs for the year range)
  await expect(page.getByRole('slider').first()).toBeVisible();

  // The Radix-era prop must not end up as a DOM attribute
  await expect(page.locator('[minstepsbetweenthumbs]')).toHaveCount(0);
});
