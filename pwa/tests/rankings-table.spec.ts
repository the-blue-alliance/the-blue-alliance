import { expect, test } from '@playwright/test';

// DataTable used to wrap every header cell — sortable or not — in a
// `<div role="button" tabIndex={0}>`, so non-sortable headers were announced as
// buttons and sortable ones relied on a hand-rolled onKeyDown. Sortable headers
// are now real <button>s; non-sortable headers get no interactive wrapper.

test('rankings table exposes sortable headers as buttons and sorts on click', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Rankings' }).click();

  // First column is Rank, which is sortable (ascending first).
  const rankHeader = page.getByRole('columnheader').first().getByRole('button');
  await expect(rankHeader).toBeVisible();
  await expect(rankHeader).toHaveAccessibleName(/Rank/);
  await expect(rankHeader).toHaveAttribute('title', 'Sort ascending');

  const rankCells = page.getByRole('row').locator('td:first-child');
  await expect(rankCells.first()).toHaveText('1');

  // Ascending matches the order the rankings arrive in, so it takes a second
  // click to reach descending and move rank 1 off the top.
  await rankHeader.click();
  await expect(rankHeader).toHaveAttribute('title', 'Sort descending');
  await expect(rankCells.first()).toHaveText('1');

  await rankHeader.click();
  await expect(rankHeader).toHaveAttribute('title', 'Clear sort');
  await expect(rankCells.first()).not.toHaveText('1');
});
