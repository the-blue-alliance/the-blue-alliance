import { expect, test } from '@playwright/test';

import { gotoHydrated } from './helpers';

test.describe('/match/2026cmptx_f1m1 videos', () => {
  test.beforeEach(async ({ page }) => {
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

    await gotoHydrated(page, '/match/2026cmptx_f1m1');
  });

  test('shows video placeholders before the browser is idle', async ({
    page,
  }) => {
    await expect(page.getByTestId('youtube-embed-placeholder')).toHaveCount(2);
  });

  test('does not load video players before the browser is idle', async ({
    page,
  }) => {
    await expect(page.locator('iframe[src*="youtube.com/embed"]')).toHaveCount(
      0,
    );
  });

  test('loads video players when the browser becomes idle', async ({
    page,
  }) => {
    await page.evaluate(() => {
      window.dispatchEvent(new Event('test-run-idle-callbacks'));
    });

    await expect(page.locator('iframe[src*="youtube.com/embed"]')).toHaveCount(
      2,
    );
  });

  test('preserves the video layout when players load', async ({ page }) => {
    const placeholderBoxes = await page
      .getByTestId('youtube-embed-placeholder')
      .evaluateAll((elements) =>
        elements.map((element) => element.getBoundingClientRect().toJSON()),
      );

    await page.evaluate(() => {
      window.dispatchEvent(new Event('test-run-idle-callbacks'));
    });

    const playerBoxes = await page
      .locator('iframe[src*="youtube.com/embed"]')
      .evaluateAll((elements) =>
        elements.map((element) => element.getBoundingClientRect().toJSON()),
      );
    expect(playerBoxes).toEqual(placeholderBoxes);
  });
});

[
  // TODO: re-enable after 2015 events are regrabbed with snake_case remap
  // (prod currently serves camelCase alliance keys until then).
  // ['2015 match', '/match/2015nyny_qm1'],
  ['2024 match', '/match/2024mil_f1m2'],
].forEach(([name, path]) => {
  test(`shows the score breakdown for a ${name}`, async ({ page }) => {
    await gotoHydrated(page, path);

    await expect(page.getByRole('table').first()).toBeVisible();
  });
});

test('renders a practice match page', async ({ page }) => {
  await page.goto('/match/2026nysu_pm5');

  await expect(
    page.getByRole('heading', { name: /Practice 5/ }).first(),
  ).toBeVisible();
});
