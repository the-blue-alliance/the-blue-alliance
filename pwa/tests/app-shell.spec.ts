import { type Page, expect, test } from '@playwright/test';

// Repeat visits: the first page load is server-rendered and installs the
// service worker, which answers later page loads with the app shell.
test.use({ serviceWorkers: 'allow' });

async function installServiceWorker(page: Page) {
  await page.goto('/about');
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
}

test.beforeEach(async ({ page }) => {
  await installServiceWorker(page);
});

test('serves a repeat visit from the service worker', async ({ page }) => {
  const response = await page.goto('/team/254');

  expect(response?.fromServiceWorker()).toBe(true);
});

test('renders the page on a repeat visit', async ({ page }) => {
  await page.goto('/team/254');

  await expect(
    page.getByRole('heading', {
      level: 1,
      name: 'Team 254 - The Cheesy Poofs',
    }),
  ).toBeVisible();
});

test('shows a loading skeleton until the page data arrives on a repeat visit', async ({
  page,
}) => {
  await page.route(
    /\/api\/v3\/team\/frc254(\?|$)/,
    () => new Promise(() => {}),
  );

  await page.goto('/team/254');

  await expect(
    page.getByRole('status', { name: 'Loading page' }),
  ).toBeVisible();
});

test('marks the current section in the navbar on a repeat visit', async ({
  page,
}) => {
  await page.goto('/events');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(
    page.getByRole('banner').getByRole('link', { name: 'Events', exact: true }),
  ).toHaveAttribute('aria-current', 'page');
});

test('links Leave beta to the current page on a repeat visit', async ({
  page,
}) => {
  await page.goto('/events');
  await page.locator('body[data-hydrated]').waitFor();

  await expect(page.getByRole('link', { name: 'Leave beta' })).toHaveAttribute(
    'href',
    'https://www.thebluealliance.com/events',
  );
});

test('loads GameDay from the server on a repeat visit', async ({ page }) => {
  const response = await page.goto('/gameday');

  expect(response?.fromServiceWorker()).toBe(false);
});
