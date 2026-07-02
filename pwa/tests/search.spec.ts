import { expect, test } from '@playwright/test';

// Regression tests for #10104: in the search modal, pressing Enter must
// navigate to the result that is highlighted — the visibly-first result for a
// freshly typed query (the bug: "1022" navigated to team 10221), and the item
// the user moved to via arrows, vim keys (Ctrl+N/J/P/K), or pointer hover. The
// search index is mocked so the colliding team numbers and a known event are
// guaranteed present and the assertions are deterministic.

const SEARCH_INDEX = {
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
    await page.route('**/search_index*', async (route) => {
      await route.fulfill({ json: SEARCH_INDEX });
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
