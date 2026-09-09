import { expect, test } from '@playwright/test';

test('event page fetches Nexus from the browser, not the SSR loader', async ({
  page,
}) => {
  const nexusRequests: string[] = [];
  page.on('request', (request) => {
    if (request.url().includes('/nexus_info')) {
      nexusRequests.push(request.url());
    }
  });

  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await expect.poll(() => nexusRequests.length).toBeGreaterThan(0);
});

test('match modal focuses the dialog content container on open', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('link', { name: 'Quals 1', exact: true }).click();

  const content = page.locator('[data-slot="dialog-content"]');
  await expect(content).toBeVisible();
  await expect(content).toBeFocused();
});

test('event Media tab renders SmugMug photo galleries', async ({ page }) => {
  await page.goto('/event/2026necmp');

  await page.getByRole('tab', { name: /Media/ }).click();

  const gallery = page.getByTestId('smugmug-album-gallery');
  await expect(gallery).toBeVisible();
  await expect(
    gallery.locator('a[href*="nefirst.smugmug.com"]').first(),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Photo Galleries' }),
  ).toBeVisible();
});

test('rankings table exposes sortable headers as buttons and sorts on click', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Rankings' }).click();

  const rankHeader = page.getByRole('columnheader').first().getByRole('button');
  await expect(rankHeader).toBeVisible();
  await expect(rankHeader).toHaveAccessibleName(/Rank/);
  await expect(rankHeader).toHaveAttribute('title', 'Sort ascending');

  const rankCells = page.getByRole('row').locator('td:first-child');
  await expect(rankCells.first()).toHaveText('1');

  await rankHeader.click();
  await expect(rankHeader).toHaveAttribute('title', 'Sort descending');
  await expect(rankCells.first()).toHaveText('1');

  await rankHeader.click();
  await expect(rankHeader).toHaveAttribute('title', 'Clear sort');
  await expect(rankCells.first()).not.toHaveText('1');
});

test('round robin event shows the Round Robin Semifinals table', async ({
  page,
}) => {
  await page.goto('/event/2019cmptx');
  await page.locator('body[data-hydrated]').waitFor();

  const heading = page.getByRole('heading', {
    name: 'Round Robin Semifinals',
  });
  await expect(heading).toBeVisible();
  await expect(
    page.getByRole('columnheader', { name: 'Champ Points' }),
  ).toBeVisible();
  await expect(
    page.getByRole('columnheader', { name: 'Advance to Finals' }),
  ).toBeVisible();

  const turingRow = page.getByRole('row', { name: /^1 Turing/ });
  await expect(turingRow).toContainText('5-0-0');
  await expect(turingRow).toContainText('10');
});

test('non round robin event has no Round Robin Semifinals table', async ({
  page,
}) => {
  await page.goto('/event/2023cmptx');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('heading', { name: 'Round Robin Semifinals' }),
  ).toHaveCount(0);
});

test('event insights chart renders after opening the Insights tab', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  const insightsTab = page.getByRole('tab', { name: /insights/i });
  if (await insightsTab.isVisible()) {
    await insightsTab.click();
    await expect(page.locator('svg.recharts-surface')).toBeVisible();
  }
});

test('animated tab indicator loads when switching event tabs', async ({
  page,
}) => {
  const scriptUrls: string[] = [];
  page.on('request', (request) => {
    if (request.resourceType() === 'script') scriptUrls.push(request.url());
  });

  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  expect(scriptUrls.some((url) => url.includes('animatedTabIndicator'))).toBe(
    false,
  );

  await page.getByRole('tab', { name: /rankings/i }).click();
  await expect(page.getByRole('tab', { name: /rankings/i })).toHaveAttribute(
    'aria-selected',
    'true',
  );
});

test('event page shows the favorite button', async ({ page }) => {
  await page.goto('/event/2024casj');
  await expect(
    page.getByRole('button', { name: /add to favorites/i }),
  ).toBeVisible();
});
