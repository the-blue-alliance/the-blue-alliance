import { expect, test } from '@playwright/test';

test('district insights team table sorts on header click', async ({ page }) => {
  await page.goto('/district/fim/insights');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Team Data' }).click();

  const teamHeader = page.getByRole('columnheader').first().getByRole('button');
  await expect(teamHeader).toBeVisible();
  await expect(teamHeader).toHaveAccessibleName(/Team/);
  await expect(teamHeader).toHaveAttribute('title', 'Sort ascending');

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
