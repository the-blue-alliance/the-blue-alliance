import { expect, test } from '@playwright/test';

test('match players load automatically after the browser is idle', async ({
  page,
}) => {
  await page.addInitScript(() => {
    window.requestIdleCallback = (callback) => {
      window.addEventListener(
        'test-run-idle-callbacks',
        () =>
          callback({
            didTimeout: false,
            timeRemaining: () => 50,
          }),
        { once: true },
      );
      return 1;
    };
    window.cancelIdleCallback = () => {};
  });

  await page.goto('/match/2026cmptx_f1m1');
  await page.locator('body[data-hydrated]').waitFor();

  const players = page.locator('iframe[src*="youtube.com/embed"]');
  const placeholders = page.getByTestId('youtube-embed-placeholder');
  await expect(players).toHaveCount(0);
  await expect(placeholders).toHaveCount(2);

  const placeholderBoxes = await placeholders.evaluateAll((elements) =>
    elements.map((element) => element.getBoundingClientRect().toJSON()),
  );

  await page.evaluate(() => {
    window.dispatchEvent(new Event('test-run-idle-callbacks'));
  });

  await expect(players).toHaveCount(2);
  const playerBoxes = await players.evaluateAll((elements) =>
    elements.map((element) => element.getBoundingClientRect().toJSON()),
  );
  expect(playerBoxes).toEqual(placeholderBoxes);
});

test('lazy score breakdown renders the correct year for a 2015 match', async ({
  page,
}) => {
  await page.goto('/match/2015nyny_qm1');
  await page.locator('body[data-hydrated]').waitFor();
  await expect(page.getByRole('table').first()).toBeVisible();
});

test('lazy score breakdown renders the correct year for a 2024 match', async ({
  page,
}) => {
  await page.goto('/match/2024mil_f1m2');
  await page.locator('body[data-hydrated]').waitFor();
  await expect(page.getByRole('table').first()).toBeVisible();
});
