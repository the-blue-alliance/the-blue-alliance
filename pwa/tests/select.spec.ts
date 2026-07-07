import { expect, test } from '@playwright/test';

// Regression tests for the Base UI Select migration:
// - Select.Value must render the selected item's label, not the raw value
//   (requires `items` on Select.Root; see resolveSelectedLabel in Base UI)
// - The popup list must not be pinned to the trigger's height
//   (--anchor-height) and must scroll when there are many options

test('teams page selector shows range labels, not raw page numbers', async ({
  page,
}) => {
  await page.goto('/teams/2');
  await page.waitForLoadState('networkidle');

  // The trigger renders the selected item's label ("1000s"), not the raw
  // value ("2")
  const trigger = page.getByRole('combobox');
  await expect(trigger).toContainText('1000s');
  await expect(trigger).not.toHaveText(/^2$/);
});

test('teams page selector opens a list taller than the trigger', async ({
  page,
}) => {
  await page.goto('/teams');
  await page.waitForLoadState('networkidle');

  const trigger = page.getByRole('combobox');
  await expect(trigger).toContainText('1-999');
  await trigger.click();

  const listbox = page.getByRole('listbox');
  await expect(listbox).toBeVisible();

  // With the list pinned to the trigger height (~40px), only the first
  // option was visible and the rest were clipped with no scrollbar.
  const options = listbox.getByRole('option');
  expect(await options.count()).toBeGreaterThan(3);
  await expect(options.nth(3)).toBeInViewport();
});

test('events page district selector shows "All Events" label', async ({
  page,
}) => {
  await page.goto('/events');
  await page.waitForLoadState('networkidle');

  // The trigger renders the "All Events" label, not the raw value "all"
  const trigger = page.getByRole('combobox').filter({ hasText: 'All Events' });
  await expect(trigger).toBeVisible();
});
