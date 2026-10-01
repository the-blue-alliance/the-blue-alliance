import { expect, test } from '@playwright/test';

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

    await page.goto('/match/2026cmptx_f1m1');
    await page.locator('body[data-hydrated]').waitFor();
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
  ['2015 match', '/match/2015nyny_qm1'],
  ['2024 match', '/match/2024mil_f1m2'],
].forEach(([name, path]) => {
  test(`shows the score breakdown for a ${name}`, async ({ page }) => {
    await page.goto(path);
    await page.locator('body[data-hydrated]').waitFor();

    await expect(page.getByRole('table').first()).toBeVisible();
  });
});
