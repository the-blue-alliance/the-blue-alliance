import { expect, test } from '@playwright/test';

test('past-year district championship page stops polling', async ({ page }) => {
  await page.clock.install();

  const eventsRequests: string[] = [];
  page.on('request', (request) => {
    if (request.url().includes('/api/v3/events/2019')) {
      eventsRequests.push(request.url());
    }
  });

  await page.goto('/district/fim/champs/2019');
  await page.locator('body[data-hydrated]').waitFor();
  await expect.poll(() => eventsRequests.length).toBeGreaterThan(0);

  const afterLoad = eventsRequests.length;
  await page.clock.fastForward('03:00');
  await page.waitForTimeout(500);

  expect(eventsRequests.length).toBe(afterLoad);
});

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

  const allowedCell = /^$|^DCMP$|^Declined (CMP|DCMP)$|^[A-Z]/;
  for (const cell of cells) {
    expect(cell).toMatch(allowedCell);
  }

  expect(cells.some((cell) => cell.length > 0)).toBe(true);
});
