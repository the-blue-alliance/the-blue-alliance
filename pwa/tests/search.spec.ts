import { expect, test } from '@playwright/test';

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
