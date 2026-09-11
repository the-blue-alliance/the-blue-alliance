import { expect, test } from '@playwright/test';

test('fetches Nexus event data in the browser', async ({ page }) => {
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

test.describe('/event/2024mil', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2024mil');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('focuses the match dialog when it opens', async ({ page }) => {
    await page.getByRole('link', { name: 'Quals 1', exact: true }).click();

    await expect(page.locator('[data-slot="dialog-content"]')).toBeFocused();
  });

  test('labels the rank column as a sorting control', async ({ page }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    await expect(
      page.getByRole('columnheader').first().getByRole('button'),
    ).toHaveAccessibleName(/Rank/);
  });

  test('offers ascending rank order before sorting', async ({ page }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    await expect(
      page.getByRole('columnheader').first().getByRole('button'),
    ).toHaveAttribute('title', 'Sort ascending');
  });

  test('shows rank one first before sorting', async ({ page }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    await expect(
      page.getByRole('row').locator('td:first-child').first(),
    ).toHaveText('1');
  });

  test('offers descending rank order after sorting ascending', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    const rankHeader = page
      .getByRole('columnheader')
      .first()
      .getByRole('button');
    await rankHeader.click();

    await expect(rankHeader).toHaveAttribute('title', 'Sort descending');
  });

  test('keeps rank one first after sorting ascending', async ({ page }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    await page.getByRole('columnheader').first().getByRole('button').click();

    await expect(
      page.getByRole('row').locator('td:first-child').first(),
    ).toHaveText('1');
  });

  test('offers clearing rank order after sorting descending', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    const rankHeader = page
      .getByRole('columnheader')
      .first()
      .getByRole('button');
    await rankHeader.click();
    await rankHeader.click();

    await expect(rankHeader).toHaveAttribute('title', 'Clear sort');
  });

  test('restores the original row order after clearing rank order', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    const rankHeader = page
      .getByRole('columnheader')
      .first()
      .getByRole('button');
    await rankHeader.click();
    await rankHeader.click();

    await expect(
      page.getByRole('row').locator('td:first-child').first(),
    ).not.toHaveText('1');
  });

  test('shows the event insights chart when the Insights tab opens', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Insights' }).click();

    await expect(page.locator('svg.recharts-surface')).toBeVisible();
  });
});

test('defers the animated tab indicator until a tab changes', async ({
  page,
}) => {
  const scriptUrls: string[] = [];
  page.on('request', (request) => {
    if (request.resourceType() === 'script') {
      scriptUrls.push(request.url());
    }
  });

  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  expect(scriptUrls.some((url) => url.includes('animatedTabIndicator'))).toBe(
    false,
  );
});

test('loads the animated tab indicator once the page is idle', async ({
  page,
}) => {
  const indicatorRequest = page.waitForRequest((request) =>
    request.url().includes('animatedTabIndicator'),
  );
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  expect((await indicatorRequest).url()).toContain('animatedTabIndicator');
});

test.describe('/event/2026necmp Media tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2026necmp');
    await page.getByRole('tab', { name: 'Media' }).click();
  });

  test('shows the photo galleries heading', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Photo Galleries' }),
    ).toBeVisible();
  });

  test('shows the SmugMug album gallery', async ({ page }) => {
    await expect(page.getByTestId('smugmug-album-gallery')).toBeVisible();
  });

  test('links to the NE FIRST SmugMug gallery', async ({ page }) => {
    await expect(
      page
        .getByTestId('smugmug-album-gallery')
        .locator('a[href*="nefirst.smugmug.com"]')
        .first(),
    ).toBeVisible();
  });
});

test.describe('/event/2019cmptx', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2019cmptx');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('shows the Round Robin Semifinals standings', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Round Robin Semifinals' }),
    ).toBeVisible();
  });

  ['Champ Points', 'Advance to Finals'].forEach((name) => {
    test(`shows the ${name} column in the round robin standings`, async ({
      page,
    }) => {
      await expect(page.getByRole('columnheader', { name })).toBeVisible();
    });
  });

  test('shows the Turing win-loss-tie record', async ({ page }) => {
    await expect(page.getByRole('row', { name: /^1 Turing/ })).toContainText(
      '5-0-0',
    );
  });

  test('shows the Turing championship points', async ({ page }) => {
    await expect(page.getByRole('row', { name: /^1 Turing/ })).toContainText(
      '10',
    );
  });
});

test('hides round robin standings for a non-round-robin event', async ({
  page,
}) => {
  await page.goto('/event/2023cmptx');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('heading', { name: 'Round Robin Semifinals' }),
  ).toHaveCount(0);
});

test('shows the favorite button for an event', async ({ page }) => {
  await page.goto('/event/2024casj');

  await expect(
    page.getByRole('button', { name: /add to favorites/i }),
  ).toBeVisible();
});

test.describe('/event/2024mil tabs and the URL hash', () => {
  test('clicking a tab puts it in the hash without a new history entry', async ({
    page,
  }) => {
    await page.goto('/event/2024mil');
    await page.locator('body[data-hydrated]').waitFor();
    await page.getByRole('tab', { name: 'Rankings' }).click();
    await expect(page).toHaveURL(/#rankings$/);
    await page.getByRole('tab', { name: 'Awards' }).click();
    await expect(page).toHaveURL(/#awards$/);
    await page.goBack();
    // Replaced, not pushed: back leaves the event page entirely
    await expect(page).not.toHaveURL(/\/event\/2024mil/);
  });

  test('opens the tab named by the hash on load', async ({ page }) => {
    await page.goto('/event/2024mil#media');
    await page.locator('body[data-hydrated]').waitFor();
    await expect(page.getByRole('tab', { name: 'Media' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });

  test("understands the old site's hash names", async ({ page }) => {
    await page.goto('/event/2024mil#event-insights');
    await page.locator('body[data-hydrated]').waitFor();
    await expect(page.getByRole('tab', { name: 'Insights' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });

  test('ignores a hash that is not a tab', async ({ page }) => {
    await page.goto('/event/2024mil#not-a-tab');
    await page.locator('body[data-hydrated]').waitFor();
    await expect(page.getByRole('tab', { name: 'Results' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
  });
});
