import { expect, test } from '@playwright/test';

test('navbar is visible', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(
    page.locator('div').filter({
      hasText: 'The Blue AlliancemyTBAEventsTeamsGameDayInsightsMore',
    }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'The Blue Alliance' }),
  ).toBeVisible();
  await expect(
    page.locator('div').filter({ hasText: 'myTBA' }).nth(2),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Events' })).toBeVisible();
  await expect(
    page.locator('div').filter({ hasText: 'Teams' }).nth(2),
  ).toBeVisible();
  await expect(
    page.locator('div').filter({ hasText: 'GameDay' }).nth(2),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Insights' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'More' })).toBeVisible();
  await expect(page.getByPlaceholder('Search')).toBeVisible();
});

test('(mobile) navbar is visible', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(page.getByLabel('Main')).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'The Blue Alliance' }),
  ).toBeVisible();
  await expect(
    page.locator('div').filter({ hasText: 'myTBA' }).nth(2),
  ).toBeVisible();
  await expect(page.locator('a').filter({ hasText: 'Events' })).toBeVisible();
  await expect(page.getByRole('button')).toBeVisible();
  await expect(page.getByPlaceholder('Search')).toBeVisible();
});
