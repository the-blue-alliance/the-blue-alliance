import { expect, test } from '@playwright/test';

test('past-year district championship tab stops polling', async ({ page }) => {
  await page.clock.install();

  const requestUrls: string[] = [];
  page.on('request', (request) => requestUrls.push(request.url()));
  const firstEventsRequest = page.waitForRequest((request) =>
    request.url().includes('/api/v3/events/2019'),
  );

  await page.goto('/district/fim/2019');
  await page.locator('body[data-hydrated]').waitFor();
  await page.getByRole('tab', { name: 'Champs' }).click();
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

test.describe('/district/fim/2024 header', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/district/fim/2024');
    await page.locator('body[data-hydrated]').waitFor();
  });

  [['Rankings'], ['Events'], ['Teams'], ['Champs']].forEach(([tabName]) => {
    test(`shows the ${tabName} tab`, async ({ page }) => {
      await expect(page.getByRole('tab', { name: tabName })).toBeVisible();
    });
  });

  [['511 teams'], ['27 events']].forEach(([summary]) => {
    test(`shows ${summary} below the title`, async ({ page }) => {
      await expect(page.getByText(summary, { exact: true })).toBeVisible();
    });
  });

  test('links to the District Championship below the title', async ({
    page,
  }) => {
    await expect(
      page.getByRole('link', { name: 'District Championship' }),
    ).toHaveAttribute('href', '/event/2024micmp');
  });

  test('links to all-time insights from the year selector', async ({
    page,
  }) => {
    await page.getByRole('button', { name: '2024' }).click();

    await expect(
      page.getByRole('menuitem', { name: 'Insights' }),
    ).toHaveAttribute('href', '/district/fim/insights');
  });

  test('shows the championship tracker in the Champs tab', async ({ page }) => {
    await page.getByRole('tab', { name: 'Champs' }).click();

    await expect(page.getByText('All Rankings')).toBeVisible();
  });
});

test.describe('/district/fim/2024 rankings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/district/fim/2024');
    await page.locator('body[data-hydrated]').waitFor();
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
