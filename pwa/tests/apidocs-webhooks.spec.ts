import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/apidocs/webhooks');
  await expect(page.locator('body[data-hydrated]')).toBeVisible();
});

test('scrolls to Alliance Selection when its table of contents link is clicked', async ({
  page,
}) => {
  await page.getByRole('link', { name: 'Alliance Selection' }).first().click();

  await expect(
    page.getByRole('heading', { name: 'Alliance Selection' }),
  ).toBeInViewport();
});

test('documents the alliances in the Alliance Selection payload', async ({
  page,
}) => {
  const section = page.locator('section#alliance_selection');

  await expect(
    section.getByRole('cell', { name: 'event_alliances', exact: true }),
  ).toBeVisible();
  const example = JSON.parse(await section.locator('pre').innerText());
  expect(example.message_data.event_alliances[0]).toEqual({
    name: 'Alliance 1',
    picks: ['frc195', 'frc558', 'frc5122'],
    declines: [],
  });
});

test('shows the verification message example', async ({ page }) => {
  await expect(
    page.getByText(
      '"verification_key": "8279a61abdeee0cf46a86136bf888188a4b18cdf"',
    ),
  ).toBeVisible();
});

test('asks signed-out users to sign in before sending a test notification', async ({
  page,
}) => {
  await expect(
    page.getByRole('link', { name: 'Sign in' }).first(),
  ).toHaveAttribute('href', '/account');
});
