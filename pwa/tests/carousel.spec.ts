import { expect, test } from '@playwright/test';

// Regression tests for the team robot-pic carousel performance work: the first
// slide loads eagerly at high priority with a resized image, later slides are
// deferred, and navigation / the original-media link still work.

const TEAM_PAGE = '/team/254/2026';

function isImgurThumb(url: string): boolean {
  return /i\.imgur\.com\/[A-Za-z0-9]{7}[lh]\.\w+(\?.*)?$/.test(url);
}

function isImgurOriginal(url: string): boolean {
  return (
    /i\.imgur\.com\/[A-Za-z0-9]+\.\w+(\?.*)?$/.test(url) && !isImgurThumb(url)
  );
}

test.describe('team robot-pic carousel', () => {
  test('first slide eager + resized, later slides deferred', async ({
    page,
  }) => {
    const imageRequests: string[] = [];
    page.on('request', (req) => {
      if (req.resourceType() === 'image') imageRequests.push(req.url());
    });

    await page.goto(TEAM_PAGE);
    await page.locator('body[data-hydrated]').waitFor();

    const carousel = page.locator('[aria-roledescription="carousel"]').first();
    await expect(carousel).toBeVisible();

    const slides = carousel.locator('[aria-roledescription="slide"]');
    const imgs = carousel.locator('img');
    const slideCount = await slides.count();
    expect(slideCount).toBeGreaterThan(3);
    expect(await imgs.count()).toBeLessThan(slideCount);

    await expect(imgs.first()).toHaveAttribute('loading', 'eager');
    await expect(imgs.first()).toHaveAttribute('fetchpriority', 'high');
    await expect(imgs.nth(1)).toHaveAttribute('loading', 'lazy');
    await expect(imgs.nth(1)).toHaveAttribute('fetchpriority', 'low');

    const firstSrc = await imgs
      .first()
      .evaluate((el) => (el as HTMLImageElement).currentSrc);
    expect(isImgurThumb(firstSrc)).toBe(true);
    expect(imageRequests).toContain(firstSrc);

    for (const url of imageRequests) {
      expect(isImgurOriginal(url)).toBe(false);
    }

    const lastSlideImgs = slides.last().locator('img');
    expect(await lastSlideImgs.count()).toBe(0);
  });

  test('navigation and the original-media link still work', async ({
    page,
  }) => {
    await page.goto(TEAM_PAGE);
    await page.locator('body[data-hydrated]').waitFor();

    const carousel = page.locator('[aria-roledescription="carousel"]').first();
    await expect(carousel).toBeVisible();

    const link = carousel.locator('a[target="_blank"]').first();
    await expect(link).toHaveAttribute('href', /^https?:\/\//);

    const slide0 = carousel.locator('[aria-roledescription="slide"]').first();
    const x = () => slide0.evaluate((el) => el.getBoundingClientRect().x);
    const startX = await x();

    const next = page.getByRole('button', { name: 'Next slide' });
    const prev = page.getByRole('button', { name: 'Previous slide' });

    await next.click();
    await expect(prev).toBeEnabled();
    await expect.poll(x).toBeLessThan(startX - 100);

    await prev.click();
    await expect.poll(x).toBeGreaterThan(startX - 100);
  });

  test('mobile: first slide is eager and later slides are lazy', async ({
    page,
  }) => {
    await page.goto(TEAM_PAGE);
    await page.locator('body[data-hydrated]').waitFor();

    const imgs = page
      .locator('[aria-roledescription="carousel"]')
      .first()
      .locator('img');
    await expect(imgs.first()).toHaveAttribute('loading', 'eager');
    await expect(imgs.first()).toHaveAttribute('fetchpriority', 'high');
    await expect(imgs.nth(1)).toHaveAttribute('loading', 'lazy');
  });
});

test.describe('team media gallery', () => {
  test('Imgur cards load resized images, not full-res originals', async ({
    page,
  }) => {
    const imgurRequests: string[] = [];
    page.on('request', (req) => {
      if (req.resourceType() === 'image' && req.url().includes('i.imgur.com')) {
        imgurRequests.push(req.url());
      }
    });

    await page.goto(TEAM_PAGE);
    await page.locator('body[data-hydrated]').waitFor();

    const gallery = page.getByTestId('team-media-gallery');
    await expect(gallery).toBeVisible();
    await gallery.locator('img').first().waitFor();
    await expect.poll(() => imgurRequests.length).toBeGreaterThan(3);

    for (const url of imgurRequests) {
      expect(isImgurOriginal(url)).toBe(false);
    }

    const link = gallery.locator('a[target="_blank"]').first();
    await expect(link).toHaveAttribute('href', /^https?:\/\//);
  });
});
