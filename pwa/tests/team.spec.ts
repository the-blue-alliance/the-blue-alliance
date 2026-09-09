import { expect, test } from '@playwright/test';

test.describe('/team/604/2024', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/604/2024');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('displays the team name', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Team 604 - Quixilver');
  });

  test('links the team location', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'San Jose, CA, USA' }),
    ).toBeVisible();
  });

  test('shows the team sponsor summary', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: 'Leland High School with 13 sponsors' }),
    ).toBeVisible();
  });

  test('shows the team rookie year', async ({ page }) => {
    await expect(page.getByText('Rookie Year: 2001')).toBeVisible();
  });

  [
    ['FRC Events', 'https://frc-events.firstinspires.org/team/604'],
    ['Statbotics', 'https://www.statbotics.io/team/604'],
  ].forEach(([name, href]) => {
    test(`links to the ${name} team page`, async ({ page }) => {
      await expect(page.getByRole('link', { name })).toHaveAttribute(
        'href',
        href,
      );
    });
  });

  [
    ['Facebook', 'https://www.facebook.com/frc604'],
    ['GitHub', 'https://github.com/frc604'],
    ['Instagram', 'https://www.instagram.com/frc604'],
    ['X', 'https://x.com/frc604'],
  ].forEach(([name, href], index) => {
    test(`links to the ${name} profile`, async ({ page }) => {
      await expect(
        page.getByRole('link', { name: 'frc604', exact: true }).nth(index),
      ).toHaveAttribute('href', href);
    });
  });

  test('links to the YouTube channel', async ({ page }) => {
    await expect(page.getByRole('link', { name: '@frc604' })).toHaveAttribute(
      'href',
      'https://www.youtube.com/@frc604',
    );
  });

  [
    ['team information', 'team-info'],
    ['Silicon Valley Regional', '2024casj'],
    ['Sacramento Regional', '2024cada'],
    ['Monterey Bay Regional', '2024camb'],
    ['Milstein Division', '2024mil'],
    ['Einstein Field', '2024cmptx'],
    ['Sunset Showdown', '2024sunshow'],
    ['Chezy Champs', '2024cc'],
  ].forEach(([name, slug]) => {
    test(`provides a table-of-contents link for ${name}`, async ({ page }) => {
      await expect(page.locator(`a[href$="#${slug}"]`)).toBeVisible();
    });
  });

  [
    ['Silicon Valley Regional', '2024casj', '/event/2024casj'],
    ['Sacramento Regional', '2024cada', '/event/2024cada'],
    ['Monterey Bay Regional', '2024camb', '/event/2024camb'],
    ['Milstein Division', '2024mil', '/event/2024mil'],
    ['Einstein Field', '2024cmptx', '/event/2024cmptx'],
    ['Sunset Showdown', '2024sunshow', '/event/2024sunshow'],
    ['Chezy Champs', '2024cc', '/event/2024cc'],
  ].forEach(([name, sectionId, href]) => {
    test(`links the ${name} event section to its event page`, async ({
      page,
    }) => {
      await expect(
        page.locator(`section[id="${sectionId}"]`).getByRole('link', { name }),
      ).toHaveAttribute('href', href);
    });
  });

  [
    [
      'Silicon Valley Regional',
      '2024casj',
      /Quality Award.*Regional Finalists/,
    ],
    [
      'Sacramento Regional',
      '2024cada',
      /Regional Winners.*Industrial Design Award sponsored by General Motors/,
    ],
    [
      'Monterey Bay Regional',
      '2024camb',
      /Regional Winners.*Innovation in Control Award.*Woodie Flowers Finalist Award/,
    ],
    [
      'Milstein Division',
      '2024mil',
      /Championship Division Winner.*Autonomous Award/,
    ],
    ['Sunset Showdown', '2024sunshow', /Finalist/],
  ].forEach(([name, sectionId, awards]) => {
    test(`shows ${name} awards in its event section`, async ({ page }) => {
      await expect(page.locator(`section[id="${sectionId}"]`)).toContainText(
        awards,
      );
    });
  });

  test('shows a watch-all-videos link for event matches', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Watch All Videos' }).first(),
    ).toBeVisible();
  });

  test('watch-all-videos links point to YouTube playlists', async ({
    page,
  }) => {
    await expect(
      page.getByRole('link', { name: 'Watch All Videos' }).first(),
    ).toHaveAttribute(
      'href',
      /^https:\/\/www\.youtube\.com\/watch_videos\?video_ids=[\w,-]+&title=.+$/,
    );
  });

  test('watch-all-videos links open in a new tab', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Watch All Videos' }).first(),
    ).toHaveAttribute('target', '_blank');
  });

  test('shows the season record summary', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      'Team 604 was 58-10-1 in official play and 78-21-1 overall in 2024.',
    );
  });

  test('does not show a district rank for a non-district team', async ({
    page,
  }) => {
    await expect(page.locator('body')).not.toContainText(', they ranked #');
  });

  test('mobile: displays the team name', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Team 604 - Quixilver');
  });

  test('mobile: displays the team location', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'San Jose, CA, USA' }),
    ).toBeVisible();
  });

  test('mobile: displays the rookie year', async ({ page }) => {
    await expect(page.getByText('Rookie Year: 2001')).toBeVisible();
  });

  test('mobile: displays the season record summary', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      'Team 604 was 58-10-1 in official play and 78-21-1 overall in 2024.',
    );
  });

  test('shows the favorite button', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /add to favorites/i }),
    ).toBeVisible();
  });

  test('opens the login dialog when the favorite button is clicked', async ({
    page,
  }) => {
    await page.getByRole('button', { name: /add to favorites/i }).click();

    await expect(page.getByText('Sign in to use myTBA')).toBeVisible();
  });
});

test.describe('/team/2713/2024', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/2713/2024');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('displays the district ranking summary', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /In the New England district, they ranked #\d+ with \d+ points\./,
    );
  });

  test('links the district ranking to the New England district page', async ({
    page,
  }) => {
    await expect(
      page.getByRole('link', { name: 'New England district' }),
    ).toHaveAttribute('href', '/district/ne/2024');
  });
});

function isImgurThumb(url: string): boolean {
  return /i\.imgur\.com\/[A-Za-z0-9]{7}[lh]\.\w+(\?.*)?$/.test(url);
}

function isImgurOriginal(url: string): boolean {
  return (
    /i\.imgur\.com\/[A-Za-z0-9]+\.\w+(\?.*)?$/.test(url) && !isImgurThumb(url)
  );
}

test.describe('/team/254/2026', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/254/2026');
    await page.locator('body[data-hydrated]').waitFor();
  });

  test('renders multiple robot picture slides', async ({ page }) => {
    await expect(
      page
        .locator('[aria-roledescription="carousel"]')
        .first()
        .locator('[aria-roledescription="slide"]')
        .nth(3),
    ).toBeVisible();
  });

  [
    ['first', 'eager', 'high'],
    ['next', 'lazy', 'low'],
  ].forEach(([position, loading, fetchPriority], index) => {
    test(`loads the ${position} robot picture with the expected priority`, async ({
      page,
    }) => {
      const image = page
        .locator('[aria-roledescription="carousel"]')
        .first()
        .locator('img')
        .nth(index);
      await expect(image).toHaveAttribute('loading', loading);
      await expect(image).toHaveAttribute('fetchpriority', fetchPriority);
    });

    test(`mobile: loads the ${position} robot picture with the expected loading strategy`, async ({
      page,
    }) => {
      await expect(
        page
          .locator('[aria-roledescription="carousel"]')
          .first()
          .locator('img')
          .nth(index),
      ).toHaveAttribute('loading', loading);
    });
  });

  test('uses a resized Imgur URL for the first robot picture', async ({
    page,
  }) => {
    const firstImage = page
      .locator('[aria-roledescription="carousel"]')
      .first()
      .locator('img')
      .first();
    const firstSrc = await firstImage.evaluate(
      (element) => (element as HTMLImageElement).currentSrc,
    );

    expect(isImgurThumb(firstSrc)).toBe(true);
  });

  test('does not render an image for the last deferred slide', async ({
    page,
  }) => {
    const lastSlide = page
      .locator('[aria-roledescription="carousel"]')
      .first()
      .locator('[aria-roledescription="slide"]')
      .last();

    await expect(lastSlide.locator('img')).toHaveCount(0);
  });

  test('links the first robot picture to its original media', async ({
    page,
  }) => {
    await expect(
      page
        .locator('[aria-roledescription="carousel"]')
        .first()
        .locator('a[target="_blank"]')
        .first(),
    ).toHaveAttribute('href', /^https?:\/\//);
  });

  test('advances to the next robot picture when next is clicked', async ({
    page,
  }) => {
    const firstSlide = page
      .locator('[aria-roledescription="carousel"]')
      .first()
      .locator('[aria-roledescription="slide"]')
      .first();
    const initialX = await firstSlide.evaluate(
      (element) => element.getBoundingClientRect().x,
    );

    await page.getByRole('button', { name: 'Next slide' }).click();

    await expect
      .poll(() =>
        firstSlide.evaluate((element) => element.getBoundingClientRect().x),
      )
      .toBeLessThan(initialX - 100);
  });

  test('returns to the first robot picture when previous is clicked', async ({
    page,
  }) => {
    const firstSlide = page
      .locator('[aria-roledescription="carousel"]')
      .first()
      .locator('[aria-roledescription="slide"]')
      .first();
    const initialX = await firstSlide.evaluate(
      (element) => element.getBoundingClientRect().x,
    );
    await page.getByRole('button', { name: 'Next slide' }).click();

    await page.getByRole('button', { name: 'Previous slide' }).click();

    await expect
      .poll(() =>
        firstSlide.evaluate((element) => element.getBoundingClientRect().x),
      )
      .toBeGreaterThan(initialX - 100);
  });

  test('displays media gallery links', async ({ page }) => {
    await expect(
      page
        .getByTestId('team-media-gallery')
        .locator('a[target="_blank"]')
        .first(),
    ).toHaveAttribute('href', /^https?:\/\//);
  });

  test('requests resized Imgur images for the media gallery', async ({
    page,
  }) => {
    await page
      .getByTestId('team-media-gallery')
      .locator('img')
      .first()
      .waitFor();
    const requestUrls = await page.evaluate(() =>
      performance.getEntriesByType('resource').map((entry) => entry.name),
    );
    const imgurRequestUrls = requestUrls.filter((url) =>
      url.includes('i.imgur.com'),
    );

    expect(imgurRequestUrls.length).toBeGreaterThan(3);
    expect(imgurRequestUrls.every((url) => !isImgurOriginal(url))).toBe(true);
  });
});
