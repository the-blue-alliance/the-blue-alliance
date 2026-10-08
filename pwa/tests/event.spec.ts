import { type Page, expect, test } from '@playwright/test';

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

  test('explains the alliance captain mark on the Rankings tab', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Rankings' }).click();

    await expect(page.getByRole('list', { name: 'Key' })).toContainText(
      'Alliance captain',
    );
  });

  test('shows the event insights chart when the Insights tab opens', async ({
    page,
  }) => {
    await page.getByRole('tab', { name: 'Insights' }).click();

    await expect(page.locator('svg.recharts-surface')).toBeVisible();
  });

  test('selects a tab whose content is still loading', async ({ page }) => {
    // Hold back the lazily loaded Insights chart so its tab suspends
    await page.route(/coprScatterChart/, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await route.continue();
    });
    await page.getByRole('tab', { name: /^Teams/ }).click();
    await page.getByRole('tab', { name: 'Insights' }).click();

    await expect(page.getByRole('tab', { name: 'Insights' })).toHaveAttribute(
      'aria-selected',
      'true',
      { timeout: 1000 },
    );
  });

  test('links to the Match13 event page', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Match13' })).toHaveAttribute(
      'href',
      'https://www.match13.com/event/2024mil',
    );
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

test('loads the animated tab indicator when a tab changes', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  const indicatorRequest = page.waitForRequest((request) =>
    request.url().includes('animatedTabIndicator'),
  );
  await page.getByRole('tab', { name: 'Rankings' }).click();

  expect((await indicatorRequest).url()).toContain('animatedTabIndicator');
});

test.describe('/event/2026necmp Media tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2026necmp');
    await page.locator('body[data-hydrated]').waitFor();
    await page.getByRole('tab', { name: 'Media' }).click();
  });

  test('shows the media count in the tab', async ({ page }) => {
    await expect(page.getByRole('tab', { name: /^Media \d+$/ })).toBeVisible();
  });

  test('links to the event media suggestion form', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Add Event Media' }),
    ).toHaveAttribute('href', '/suggest/event/media?event_key=2026necmp');
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

test.describe('/event/2015rismi', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2015rismi');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('shows playoff advancement below the playoff matches', async ({
    page,
  }) => {
    await expect(
      page
        .locator('#playoff-matches')
        .getByRole('heading', { name: 'Playoff Advancement' }),
    ).toBeVisible();
  });

  test('shows the quarterfinal advancement standings', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Quarterfinals' }),
    ).toBeVisible();
  });

  test('shows the semifinal advancement standings', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Semifinals' }),
    ).toBeVisible();
  });
});

test('hides average-score advancement for a non-2015-format event', async ({
  page,
}) => {
  await page.goto('/event/2024mil');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('heading', { name: 'Playoff Advancement' }),
  ).toHaveCount(0);
});

test('shows practice matches on the Practice tab', async ({ page }) => {
  await page.goto('/event/2026nysu');
  await page.locator('body[data-hydrated]').waitFor();

  await page.getByRole('tab', { name: 'Practice' }).click();

  await expect(
    page.getByRole('link', { name: 'Practice 5', exact: true }),
  ).toBeVisible();
});

test('skips the practice matches request for an offseason event', async ({
  page,
}) => {
  const practiceRequests: string[] = [];
  page.on('request', (request) => {
    if (request.url().includes('/matches/practice')) {
      practiceRequests.push(request.url());
    }
  });

  await page.goto('/event/2024cc');
  await page.locator('body[data-hydrated]').waitFor();

  expect(practiceRequests).toEqual([]);
});

test('hides the practice tab for an offseason event', async ({ page }) => {
  await page.goto('/event/2024cc');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(page.getByRole('tab', { name: 'Practice' })).toHaveCount(0);
});

test('shows the favorite button for an event', async ({ page }) => {
  await page.goto('/event/2024casj');

  await expect(
    page.getByRole('button', { name: /add to favorites/i }),
  ).toBeVisible();
});

async function openQuixilverDialog(page: Page) {
  await page.getByRole('searchbox', { name: 'Search teams' }).fill('Quixilver');
  await page.getByRole('button', { name: '604 - Quixilver' }).click();
}

test.describe('event teams directory', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/event/2024mil');
    await page.locator('body[data-hydrated]').waitFor();
    await page.getByRole('tab', { name: /^Teams/ }).click();
    await page.getByRole('searchbox', { name: 'Search teams' }).waitFor();
  });

  ['', ' mobile'].forEach((viewport) => {
    test(`filters teams by name${viewport}`, async ({ page }) => {
      await page
        .getByRole('searchbox', { name: 'Search teams' })
        .fill('Quixilver');

      await expect(
        page.getByRole('region', { name: 'Event teams' }).getByRole('listitem'),
      ).toHaveCount(1);
    });

    test(`opens the team dialog from row whitespace${viewport}`, async ({
      page,
    }) => {
      await page
        .getByRole('searchbox', { name: 'Search teams' })
        .fill('Quixilver');
      const row = page
        .getByRole('region', { name: 'Event teams' })
        .getByRole('listitem');
      const bounds = await row.boundingBox();
      if (!bounds) throw new Error('Team row is not visible');
      await row.click({
        position: { x: bounds.width / 2, y: bounds.height - 2 },
      });

      await expect(
        page.getByRole('dialog', { name: 'Team 604 — Quixilver' }),
      ).toBeVisible();
    });

    test(`shows the team's matches in the dialog${viewport}`, async ({
      page,
    }) => {
      await openQuixilverDialog(page);

      await expect(
        page
          .getByRole('dialog')
          .getByRole('link', { name: /^Quals \d+$/ })
          .first(),
      ).toBeVisible();
    });

    test(`keeps location clicks separate from team navigation${viewport}`, async ({
      page,
    }) => {
      await page
        .getByRole('searchbox', { name: 'Search teams' })
        .fill('Quixilver');
      const popupPromise = page.waitForEvent('popup');
      await page
        .getByRole('region', { name: 'Event teams' })
        .getByRole('link', { name: 'San Jose, CA, USA' })
        .click();
      const popup = await popupPromise;
      await popup.waitForLoadState('domcontentloaded');

      expect(new URL(page.url()).pathname).toBe('/event/2024mil');
      expect(popup.url()).toMatch(/google\.com\/maps|maps\.google\.com/);
    });

    test(`restores teams when search is cleared${viewport}`, async ({
      page,
    }) => {
      await page
        .getByRole('searchbox', { name: 'Search teams' })
        .fill('Quixilver');
      await page.getByRole('button', { name: 'Clear search' }).click();

      await expect(
        page.getByRole('region', { name: 'Event teams' }).getByRole('listitem'),
      ).toHaveCount(75);
    });
  });

  test('keeps the video link clear of the break label in the team dialog mobile', async ({
    page,
  }) => {
    await openQuixilverDialog(page);
    const dialog = page.getByRole('dialog');
    const label = await dialog
      .getByText('Qualifications', { exact: true })
      .boundingBox();
    const link = await dialog
      .getByRole('link', { name: 'Watch All Videos' })
      .boundingBox();
    if (!label || !link) throw new Error('Break row is not visible');

    expect(label.x + label.width).toBeLessThanOrEqual(link.x);
  });
});

test('shows historical teams without avatars', async ({ page }) => {
  await page.goto('/event/2017casj');
  await page.locator('body[data-hydrated]').waitFor();
  await page.getByRole('tab', { name: /^Teams/ }).click();
  await page.getByRole('searchbox', { name: 'Search teams' }).fill('254');

  await expect(
    page.getByRole('button', { name: '254 - The Cheesy Poofs' }),
  ).toBeVisible();
  await expect(
    page
      .getByRole('region', { name: 'Event teams' })
      .getByRole('img', { name: 'Team Avatar' }),
  ).toHaveCount(0);
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
