import { expect, test } from '@playwright/test';

// Round robin championship events (playoff_type ROUND_ROBIN_6_TEAM) render a
// "Round Robin Semifinals" standings table below the Alliances table on the
// Results tab, fed by the getEventPlayoffAdvancement query.

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
