import { expect, test } from '@playwright/test';

// The team data table used to be a private copy of DataTable with plain
// clickable header cells. It now uses the shared DataTable, so its sortable
// headers are real <button>s with sort-direction titles.

test('district insights team table sorts on header click', async ({ page }) => {
  await page.goto('/district/fim/insights');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Team Data' }).click();

  const teamHeader = page.getByRole('columnheader').first().getByRole('button');
  await expect(teamHeader).toBeVisible();
  await expect(teamHeader).toHaveAccessibleName(/Team/);
  await expect(teamHeader).toHaveAttribute('title', 'Sort ascending');

  // Rows arrive sorted by team number, so the first click keeps rank order and
  // the second one reverses it.
  const teamCells = page.getByRole('row').locator('td:first-child');
  await expect(teamCells.first()).toHaveText(/^\d+$/);
  const lowestTeam = Number(await teamCells.first().textContent());

  await teamHeader.click();
  await expect(teamHeader).toHaveAttribute('title', 'Sort descending');
  await expect(teamCells.first()).toHaveText(String(lowestTeam));

  await teamHeader.click();
  await expect(teamHeader).toHaveAttribute('title', 'Clear sort');
  await expect(teamCells.first()).toHaveText(/^\d+$/);
  expect(Number(await teamCells.first().textContent())).toBeGreaterThan(
    lowestTeam,
  );
});
