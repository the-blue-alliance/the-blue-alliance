import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.locator('body[data-hydrated]').waitFor();
});

// Navbar

test('navbar logo link is visible', async ({ page }) => {
  await expect(page.locator('nav')).toBeVisible();
  await expect(
    page.getByRole('link', {
      name: 'The Blue Alliance Logo The Blue Alliance',
    }),
  ).toBeVisible();
});

test('navbar nav links are visible', async ({ page }) => {
  await expect(page.getByRole('link', { name: 'myTBA' })).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Events', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Teams' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'GameDay' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Insights' })).toBeVisible();
});

test('navbar search button is visible', async ({ page }) => {
  await expect(
    page.getByRole('button', { name: 'Search teams and events...' }),
  ).toBeVisible();
});

// (mobile) Navbar

test('(mobile) navbar logo link is visible', async ({ page }) => {
  await expect(page.locator('nav')).toBeVisible();
  await expect(
    page.getByRole('link', {
      name: 'The Blue Alliance Logo The Blue Alliance',
    }),
  ).toBeVisible();
});

test('(mobile) navbar shows a toggle menu button instead of nav links', async ({
  page,
}) => {
  await expect(page.getByRole('button', { name: 'Toggle Menu' })).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Events', exact: true }),
  ).not.toBeVisible();
});

test('(mobile) navbar search button is visible', async ({ page }) => {
  await expect(page.getByRole('button', { name: 'Search' })).toBeVisible();
});

// This Week's Events
// commented out while we figure out how to stub/mock properly

// test("this week's events table is visible", async ({ page }) => {
//   await expect(
//     page.getByRole('heading', { name: "This Week's Events" }),
//   ).toBeVisible();
//   await expect(page.getByRole('table')).toBeVisible();
//   await expect(page.getByRole('columnheader', { name: 'Event' })).toBeVisible();
//   await expect(
//     page.getByRole('columnheader', { name: 'Webcast' }),
//   ).toBeVisible();
//   await expect(page.getByRole('columnheader', { name: 'Dates' })).toBeVisible();
// });

// test("this week's events table rows link to event pages", async ({ page }) => {
//   const firstEventLink = page.getByRole('table').getByRole('link').first();
//   await expect(firstEventLink).toBeVisible();
//   const href = await firstEventLink.getAttribute('href');
//   expect(href).toMatch(/^\/event\//);
// });

// Footer

test('footer links are present', async ({ page }) => {
  const footer = page.getByRole('contentinfo');
  await expect(footer.getByRole('link', { name: 'GitHub' })).toBeVisible();
  await expect(footer.getByRole('link', { name: 'About us' })).toBeVisible();
  await expect(footer.getByRole('link', { name: 'Donate' })).toBeVisible();
  await expect(footer.getByRole('link', { name: 'Contact' })).toBeVisible();
  await expect(
    footer.getByRole('link', { name: 'Privacy Policy' }),
  ).toBeVisible();
  await expect(
    footer.getByRole('link', { name: 'API Documentation' }),
  ).toBeVisible();
});

test('footer toggle theme button is visible', async ({ page }) => {
  await expect(
    page.getByRole('button', { name: 'Toggle Theme' }),
  ).toBeVisible();
});

test('footer displays platinum sponsor AndyMark', async ({ page }) => {
  await expect(page.getByText('Thanks to our platinum sponsor')).toBeVisible();
  await expect(page.getByRole('link', { name: 'AndyMark' })).toBeVisible();
});

test('nav popup portal is not mounted while the menu is closed', async ({
  page,
}) => {
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.locator('[data-slot="navigation-menu-viewport"]'),
  ).toHaveCount(0);
});

test.describe('hamburger menu (narrow viewport)', () => {
  test.use({ viewport: { width: 500, height: 800 } });

  test('does not open on hover', async ({ page }) => {
    await page.goto('/');
    await page.locator('body[data-hydrated]').waitFor();

    const trigger = page.getByRole('button', { name: 'Toggle Menu' });
    await trigger.hover();
    await page.waitForTimeout(400);

    await expect(
      page.locator('[data-slot="navigation-menu-viewport"]'),
    ).toHaveCount(0);
  });

  test('opens on click and fully unmounts on second click', async ({
    page,
  }) => {
    await page.goto('/');
    await page.locator('body[data-hydrated]').waitFor();

    const trigger = page.getByRole('button', { name: 'Toggle Menu' });
    await trigger.click();

    const viewport = page.locator('[data-slot="navigation-menu-viewport"]');
    await expect(viewport).toHaveCount(1);
    await expect(viewport.getByRole('link').first()).toBeVisible();

    await trigger.click();
    await expect(
      page.locator('[data-slot="navigation-menu-viewport"]'),
    ).toHaveCount(0);
  });
});

const MOCK_SEARCH_INDEX = {
  teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
  events: [{ key: '2024casj', name: 'Silicon Valley Regional' }],
};

test('search dialog opens while search_index is still loading', async ({
  page,
}) => {
  let releaseSearchIndex!: () => void;
  const searchIndexGate = new Promise<void>((resolve) => {
    releaseSearchIndex = resolve;
  });

  await page.route('**/api/v3/search_index**', async (route) => {
    await searchIndexGate;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_SEARCH_INDEX),
    });
  });

  await page.goto('/');
  await page.locator('body[data-hydrated]').waitFor();

  const searchButton = page.getByRole('button', {
    name: 'Search teams and events...',
  });
  await expect(searchButton).toBeVisible();
  await expect(searchButton).toBeEnabled();
  await searchButton.click();

  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();

  const input = dialog.getByPlaceholder('Search teams and events...');
  await expect(input).toBeEnabled();
  await expect(dialog.getByTestId('search-index-loading')).toBeVisible();

  releaseSearchIndex();

  await expect(dialog.getByTestId('search-index-loading')).toBeHidden();
  await input.fill('254');
  await expect(dialog.getByText('254 - The Cheesy Poofs')).toBeVisible();
});

test('search trigger stays enabled while search_index is pending', async ({
  page,
}) => {
  let releaseSearchIndex!: () => void;
  const searchIndexGate = new Promise<void>((resolve) => {
    releaseSearchIndex = resolve;
  });

  await page.route('**/api/v3/search_index**', async (route) => {
    await searchIndexGate;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_SEARCH_INDEX),
    });
  });

  await page.goto('/');
  await page.locator('body[data-hydrated]').waitFor();

  const searchButton = page.getByRole('button', {
    name: 'Search teams and events...',
  });
  await expect(searchButton).toBeEnabled();
  releaseSearchIndex();
});

test('(mobile) opening search focuses the input', async ({ page }) => {
  await page.route('**/api/v3/search_index**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_SEARCH_INDEX),
    });
  });

  await page.goto('/');
  await page.locator('body[data-hydrated]').waitFor();

  const searchButton = page.getByRole('button', { name: 'Search' });
  await searchButton.click();

  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();

  const input = dialog.getByPlaceholder('Search teams and events...');
  await expect(input).toBeFocused();
});

test.describe('Dark mode toggle', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => localStorage.removeItem('theme'));
    await page.reload();
    await page.locator('footer').scrollIntoViewIfNeeded();
    await page.waitForSelector(
      '[aria-label="Toggle Theme"][data-mounted="true"]',
    );
  });

  test('toggle changes theme to dark mode', async ({ page }) => {
    const html = page.locator('html');
    await page.getByRole('button', { name: 'Toggle Theme' }).click();
    await expect(html).toHaveClass(/dark/);
  });

  test('toggle changes theme to light mode', async ({ page }) => {
    const html = page.locator('html');
    const toggleButton = page.getByRole('button', { name: 'Toggle Theme' });

    await toggleButton.click();
    await expect(html).toHaveClass(/dark/);
    await toggleButton.click();

    await expect(html).not.toHaveClass(/dark/);
  });

  test('theme persists across page reload', async ({ page }) => {
    const html = page.locator('html');
    await page.getByRole('button', { name: 'Toggle Theme' }).click();
    await expect(html).toHaveClass(/dark/);

    await page.reload();

    await expect(html).toHaveClass(/dark/);
  });

  test('theme persists after navigation', async ({ page }) => {
    const html = page.locator('html');
    await page.getByRole('button', { name: 'Toggle Theme' }).click();
    await expect(html).toHaveClass(/dark/);

    await page
      .locator('footer')
      .getByRole('link', { name: 'About us' })
      .click();
    await page.waitForURL('/about');

    await expect(html).toHaveClass(/dark/);
  });
});

test('production build does not render TanStack devtools', async ({ page }) => {
  await page.locator('body[data-hydrated]').waitFor();

  await expect(page.locator('[class*="TanStackRouterDevtools"]')).toHaveCount(
    0,
  );
  await expect(page.locator('.tsqd-open-btn-container')).toHaveCount(0);
});

// Regression tests for #10104: in the search modal, pressing Enter must
// navigate to the result that is highlighted — the visibly-first result for a
// freshly typed query (the bug: "1022" navigated to team 10221), and the item
// the user moved to via arrows, vim keys (Ctrl+N/J/P/K), or pointer hover. The
// search index is mocked so the colliding team numbers and a known event are
// guaranteed present and the assertions are deterministic.

const COLLIDING_SEARCH_INDEX = {
  teams: [
    { key: 'frc1022', nickname: 'Titan Robotics' },
    { key: 'frc10221', nickname: 'RoboLords' },
    { key: 'frc254', nickname: 'The Cheesy Poofs' },
    { key: 'frc2543', nickname: 'PETRONAS Mustangs' },
  ],
  events: [{ key: '2024casj', name: 'Silicon Valley Regional' }],
};

test.describe('search modal navigation (#10104)', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v3/search_index**', async (route) => {
      await route.fulfill({ json: COLLIDING_SEARCH_INDEX });
    });
    await page.goto('/');
    await page.locator('body[data-hydrated]').waitFor();
    await page
      .getByRole('button', { name: 'Search teams and events...' })
      .click();
    await expect(
      page.getByPlaceholder('Search teams and events...'),
    ).toBeFocused();
  });

  test('typing a team number navigates to that exact team, not the next one', async ({
    page,
  }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    // Type then immediately commit, with no settle time, to hit the race window.
    await input.pressSequentially('1022');
    await input.press('Enter');
    await expect(page).toHaveURL(/\/team\/1022$/);
  });

  test('typing a longer team number still reaches the longer team', async ({
    page,
  }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    await input.pressSequentially('10221');
    await input.press('Enter');
    await expect(page).toHaveURL(/\/team\/10221$/);
  });

  test('arrowing to a lower result and pressing Enter honors that selection', async ({
    page,
  }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    await input.pressSequentially('254');
    await expect(page.getByRole('option', { name: /2543/ })).toBeVisible();
    await input.press('ArrowDown');
    await expect(page.getByRole('option', { name: /2543/ })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await input.press('Enter');
    await expect(page).toHaveURL(/\/team\/2543$/);
  });

  test('vim-key navigation (Ctrl+N) and Enter honors the moved selection', async ({
    page,
  }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    await input.pressSequentially('254');
    await expect(page.getByRole('option', { name: /2543/ })).toBeVisible();
    await input.press('Control+n');
    await expect(page.getByRole('option', { name: /2543/ })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await input.press('Enter');
    await expect(page).toHaveURL(/\/team\/2543$/);
  });

  test('hovering a result then pressing Enter honors the hovered item', async ({
    page,
  }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    await input.pressSequentially('254');
    const lower = page.getByRole('option', { name: /2543/ });
    await expect(lower).toBeVisible();
    await lower.hover();
    await expect(lower).toHaveAttribute('aria-selected', 'true');
    await input.press('Enter');
    await expect(page).toHaveURL(/\/team\/2543$/);
  });

  test('typing an event key navigates to that event', async ({ page }) => {
    const input = page.getByPlaceholder('Search teams and events...');
    await input.pressSequentially('2024casj');
    await input.press('Enter');
    await expect(page).toHaveURL(/\/event\/2024casj$/);
  });
});
