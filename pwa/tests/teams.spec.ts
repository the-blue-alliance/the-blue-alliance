import { expect, test } from '@playwright/test';

test('teams page selector shows range labels, not raw page numbers', async ({
  page,
}) => {
  await page.goto('/teams/2');
  await page.locator('body[data-hydrated]').waitFor();

  const trigger = page.getByRole('combobox');
  await expect(trigger).toContainText('1000s');
  await expect(trigger).not.toHaveText(/^2$/);
});

test('teams page selector opens a list taller than the trigger', async ({
  page,
}) => {
  await page.goto('/teams');
  await page.locator('body[data-hydrated]').waitFor();

  const trigger = page.getByRole('combobox');
  await expect(trigger).toContainText('1-999');
  await trigger.click();

  const listbox = page.getByRole('listbox');
  await expect(listbox).toBeVisible();

  const options = listbox.getByRole('option');
  expect(await options.count()).toBeGreaterThan(3);
  await expect(options.nth(3)).toBeInViewport();
});
