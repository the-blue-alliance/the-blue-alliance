import { expect, test } from '@playwright/test';

// The district Rankings tab gained an "Advancement" column fed by the
// getDistrictAdvancement query: a green badge with the CMP qualification method,
// a red "Declined CMP"/"Declined DCMP" badge, a grey "DCMP" badge for teams that
// scored DCMP points, or an empty cell. Advancement data may be missing for a
// district, in which case every cell is empty.

const ALLOWED_CELL = /^$|^DCMP$|^Declined (CMP|DCMP)$|^[A-Z]/;

test('district rankings table shows the Advancement column', async ({
  page,
}) => {
  await page.goto('/district/fim/2024');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Rankings' }).click();

  const header = page.getByRole('columnheader', { name: 'Advancement' });
  await expect(header).toBeVisible();

  const rows = page.getByRole('row');
  const rowCount = await rows.count();
  const cells: string[] = [];
  for (let i = 1; i < rowCount; i++) {
    cells.push(
      (await rows.nth(i).getByRole('cell').last().textContent())?.trim() ?? '',
    );
  }

  for (const cell of cells) {
    expect(cell).toMatch(ALLOWED_CELL);
  }

  expect(cells.some((cell) => cell.length > 0)).toBe(true);
});
