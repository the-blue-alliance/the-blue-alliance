import { expect, test } from '@playwright/test';

test('past-year district championship page stops polling', async ({ page }) => {
  await page.clock.install();

  const requestUrls: string[] = [];
  page.on('request', (request) => requestUrls.push(request.url()));
  const firstEventsRequest = page.waitForRequest((request) =>
    request.url().includes('/api/v3/events/2019'),
  );

  await page.goto('/district/fim/champs/2019');
  await page.locator('body[data-hydrated]').waitFor();
  await firstEventsRequest;

  const eventsRequestCount = requestUrls.filter((url) =>
    url.includes('/api/v3/events/2019'),
  ).length;
  await page.clock.fastForward('03:00');
  await page.waitForTimeout(500);

  expect(
    requestUrls.filter((url) => url.includes('/api/v3/events/2019')),
  ).toHaveLength(eventsRequestCount);
});

test.describe('/district/fim/2024 rankings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/district/fim/2024');
    await page.locator('body[data-hydrated]').waitFor();
    await page.getByRole('tab', { name: 'Rankings' }).click();
  });

  test('shows the Advancement column', async ({ page }) => {
    await expect(
      page.getByRole('columnheader', { name: 'Advancement' }),
    ).toBeVisible();
  });

  test('shows an advancement status for qualifying teams', async ({ page }) => {
    const advancementStatuses = await page
      .locator('tbody tr td:last-child')
      .allTextContents();

    expect(advancementStatuses.some((status) => status.trim().length > 0)).toBe(
      true,
    );
  });

  test('uses recognized advancement status labels', async ({ page }) => {
    const advancementStatuses = await page
      .locator('tbody tr td:last-child')
      .allTextContents();
    const allowedStatus = /^$|^DCMP$|^Declined (CMP|DCMP)$|^[A-Z]/;

    expect(
      advancementStatuses.every((status) => allowedStatus.test(status.trim())),
    ).toBe(true);
  });
});

test.describe('district page tabs and the URL hash', () => {
  test('clicking a tab puts it in the hash', async ({ page }) => {
    await page.goto('/district/fim/2024');
    await page.locator('body[data-hydrated]').waitFor();
    await page.getByRole('tab', { name: 'Teams' }).click();
    await expect(page).toHaveURL(/#teams$/);
  });

  test('opens the tab named by the hash on load', async ({ page }) => {
    await page.goto('/district/fim/2024#events');
    await page.locator('body[data-hydrated]').waitFor();
    await expect(page.getByRole('tab', { name: 'Events' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });
});

test.describe('district champs page division tabs and the URL hash', () => {
  test('a division tab round-trips through the hash', async ({ page }) => {
    await page.goto('/district/fim/champs/2019');
    await page.locator('body[data-hydrated]').waitFor();
    // Division tabs follow the two fixed ones and are named from data
    const division = page.getByRole('tab').nth(2);
    const name = (await division.textContent())?.trim() ?? '';
    expect(name).not.toBe('');
    await division.click();
    await expect(page).toHaveURL(new RegExp(`#${encodeURIComponent(name)}$`));

    await page.goto(`/district/fim/champs/2019#${encodeURIComponent(name)}`);
    await page.locator('body[data-hydrated]').waitFor();
    await expect(page.getByRole('tab', { name, exact: true })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });
});
