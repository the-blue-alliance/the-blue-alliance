import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
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
  await expect(page.getByRole('link', { name: 'Events' })).toBeVisible();
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
  await expect(page.getByRole('link', { name: 'Events' })).not.toBeVisible();
});

// This Week's Events

test("this week's events table is visible", async ({ page }) => {
  await expect(
    page.getByRole('heading', { name: "This Week's Events" }),
  ).toBeVisible();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Event' })).toBeVisible();
  await expect(
    page.getByRole('columnheader', { name: 'Webcast' }),
  ).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Dates' })).toBeVisible();
});

test("this week's events table rows link to event pages", async ({ page }) => {
  const firstEventLink = page.getByRole('table').getByRole('link').first();
  await expect(firstEventLink).toBeVisible();
  const href = await firstEventLink.getAttribute('href');
  expect(href).toMatch(/^\/event\//);
});

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
