import { expect, test } from '@playwright/test';

test.describe('/team/604/2024', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/604/2024');
  });

  test('Header', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Team 604 - Quixilver');
    await expect(
      page.getByRole('link', { name: 'San Jose, CA, USA' }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Leland High School with 13 sponsors' }),
    ).toBeVisible();
    await expect(page.getByText('Rookie Year: 2001')).toBeVisible();

    const frcEventsLink = page.getByRole('link', { name: 'FRC Events' });
    await expect(frcEventsLink).toBeVisible();
    await expect(frcEventsLink).toHaveAttribute(
      'href',
      'https://frc-events.firstinspires.org/team/604',
    );

    const statboticsLink = page.getByRole('link', { name: 'Statbotics' });
    await expect(statboticsLink).toBeVisible();
    await expect(statboticsLink).toHaveAttribute(
      'href',
      'https://www.statbotics.io/team/604',
    );
  });

  test('Social media', async ({ page }) => {
    const facebook = page
      .getByRole('link', {
        name: 'frc604',
      })
      .first();
    await expect(facebook).toBeVisible();
    await expect(facebook).toHaveAttribute(
      'href',
      'https://www.facebook.com/frc604',
    );

    const github = page.getByRole('link', { name: 'frc604' }).nth(1);
    await expect(github).toBeVisible();
    await expect(github).toHaveAttribute('href', 'https://github.com/frc604');

    const instagram = page.getByRole('link', { name: 'frc604' }).nth(2);
    await expect(instagram).toBeVisible();
    await expect(instagram).toHaveAttribute(
      'href',
      'https://www.instagram.com/frc604',
    );

    const twitter = page.getByRole('link', { name: 'frc604' }).nth(3);
    await expect(twitter).toBeVisible();
    await expect(twitter).toHaveAttribute('href', 'https://x.com/frc604');

    const youtube = page.getByRole('link', { name: '@frc604' });
    await expect(youtube).toBeVisible();
    await expect(youtube).toHaveAttribute(
      'href',
      'https://www.youtube.com/@frc604',
    );
  });

  test('Event sidebar', async ({ page }) => {
    // TOC sidebar links use hash fragments pointing to section IDs
    await expect(page.locator('a[href$="#team-info"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024casj"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024cada"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024camb"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024mil"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024cmptx"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024sunshow"]')).toBeVisible();
    await expect(page.locator('a[href$="#2024cc"]')).toBeVisible();
  });

  test('Event sections', async ({ page }) => {
    const svLink = page.getByRole('link', { name: 'Silicon Valley Regional' });
    await expect(svLink).toBeVisible();
    await expect(svLink).toHaveAttribute('href', '/event/2024casj');

    const sacLink = page.getByRole('link', { name: 'Sacramento Regional' });
    await expect(sacLink).toBeVisible();
    await expect(sacLink).toHaveAttribute('href', '/event/2024cada');

    const mbLink = page.getByRole('link', { name: 'Monterey Bay Regional' });
    await expect(mbLink).toBeVisible();
    await expect(mbLink).toHaveAttribute('href', '/event/2024camb');

    const milLink = page.getByRole('link', { name: 'Milstein Division' });
    await expect(milLink).toBeVisible();
    await expect(milLink).toHaveAttribute('href', '/event/2024mil');

    const einsteinLink = page.getByRole('link', { name: 'Einstein Field' });
    await expect(einsteinLink).toBeVisible();
    await expect(einsteinLink).toHaveAttribute('href', '/event/2024cmptx');

    // Sunset Showdown and Chezy Champs also appear as TOC links, so scope to h2
    const sunsetH2 = page.getByRole('heading', {
      name: 'Sunset Showdown',
      level: 2,
    });
    const sunsetLink = sunsetH2.getByRole('link');
    await expect(sunsetLink).toBeVisible();
    await expect(sunsetLink).toHaveAttribute('href', '/event/2024sunshow');

    const chezyH2 = page.getByRole('heading', {
      name: 'Chezy Champs',
      level: 2,
    });
    const chezyLink = chezyH2.getByRole('link');
    await expect(chezyLink).toBeVisible();
    await expect(chezyLink).toHaveAttribute('href', '/event/2024cc');
  });

  test('Awards', async ({ page }) => {
    // Each event section has an id matching the event key
    // Note: CSS IDs starting with digits are invalid in CSS, so use [id="..."]
    const svSection = page.locator('section[id="2024casj"]');
    await expect(svSection.getByText('Quality Award')).toBeVisible();
    await expect(svSection.getByText('Regional Finalists')).toBeVisible();

    const sacSection = page.locator('section[id="2024cada"]');
    await expect(sacSection.getByText('Regional Winners')).toBeVisible();
    await expect(
      sacSection.getByText(
        'Industrial Design Award sponsored by General Motors',
      ),
    ).toBeVisible();

    const mbSection = page.locator('section[id="2024camb"]');
    await expect(mbSection.getByText('Regional Winners')).toBeVisible();
    await expect(
      mbSection.getByText('Innovation in Control Award'),
    ).toBeVisible();
    await expect(
      mbSection
        .locator('li')
        .filter({ hasText: 'Woodie Flowers Finalist Award' }),
    ).toBeVisible();

    const milSection = page.locator('section[id="2024mil"]');
    await expect(
      milSection.getByText('Championship Division Winner'),
    ).toBeVisible();
    await expect(milSection.getByText('Autonomous Award')).toBeVisible();

    const sunsetSection = page.locator('section[id="2024sunshow"]');
    await expect(sunsetSection.getByText('Finalist')).toBeVisible();
  });

  test('Stats summary', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      'Team 604 was 58-10-1 in official play and 78-21-1 overall in 2024.',
    );
  });

  test('Stats details', async ({ page }) => {
    await page.getByText('Show Details').click();

    await expect(
      page.getByTestId('test_Official Events').locator('dt'),
    ).toHaveText('Official Events');
    await expect(
      page.getByTestId('test_Official Events').locator('dd'),
    ).toHaveText('5');

    await expect(
      page.getByTestId('test_Official Matches').locator('dt'),
    ).toHaveText('Official Matches');
    await expect(
      page.getByTestId('test_Official Matches').locator('dd'),
    ).toHaveText('69');

    await expect(page.getByTestId('test_Awards').locator('dt')).toHaveText(
      'Awards',
    );
    await expect(page.getByTestId('test_Awards').locator('dd')).toHaveText(
      '10',
    );

    await expect(page.getByTestId('test_High Score').locator('dt')).toHaveText(
      'High Score',
    );
    await expect(page.getByTestId('test_High Score').locator('dd')).toHaveText(
      '153',
    );

    await expect(page.getByTestId('official_quals_cell')).toHaveText('38-5-1');
    await expect(page.getByTestId('official_playoff_cell')).toHaveText(
      '20-5-0',
    );
    await expect(page.getByTestId('official_overall_cell')).toHaveText(
      '58-10-1',
    );

    await expect(page.getByTestId('unofficial_quals_cell')).toHaveText(
      '14-6-0',
    );
    await expect(page.getByTestId('unofficial_playoff_cell')).toHaveText(
      '6-5-0',
    );
    await expect(page.getByTestId('unofficial_overall_cell')).toHaveText(
      '20-11-0',
    );

    await expect(page.getByTestId('combined_quals_cell')).toHaveText('52-11-1');
    await expect(page.getByTestId('combined_playoff_cell')).toHaveText(
      '26-10-0',
    );
    await expect(page.getByTestId('combined_overall_cell')).toHaveText(
      '78-21-1',
    );
  });

  test('Stats details winrate tooltips', async ({ page }) => {
    await page.getByText('Show Details').click();

    await page.getByTestId('official_quals_cell').hover();
    await expect(
      page.getByTestId('official_quals_tooltip').first(),
    ).toContainText('86% winrate');

    await page.getByTestId('official_playoff_cell').hover();
    await expect(page.getByTestId('official_playoff_tooltip')).toContainText(
      '80% winrate',
    );

    await page.getByTestId('official_overall_cell').hover();
    await expect(
      page.getByTestId('official_overall_tooltip').first(),
    ).toContainText('84% winrate');

    await page.getByTestId('unofficial_quals_cell').hover();
    await expect(page.getByTestId('unofficial_quals_tooltip')).toContainText(
      '70% winrate',
    );

    await page.getByTestId('unofficial_playoff_cell').hover();
    await expect(page.getByTestId('unofficial_playoff_tooltip')).toContainText(
      '55% winrate',
    );

    await page.getByTestId('unofficial_overall_cell').hover();
    await expect(page.getByTestId('unofficial_overall_tooltip')).toContainText(
      '65% winrate',
    );

    await page.getByTestId('combined_quals_cell').hover();
    await expect(page.getByTestId('combined_quals_tooltip')).toContainText(
      '81% winrate',
    );

    await page.getByTestId('combined_playoff_cell').hover();
    await expect(page.getByTestId('combined_playoff_tooltip')).toContainText(
      '72% winrate',
    );

    await page.getByTestId('combined_overall_cell').hover();
    await expect(page.getByTestId('combined_overall_tooltip')).toContainText(
      '78% winrate',
    );
  });

  test('mobile: Header', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Team 604 - Quixilver');
    await expect(
      page.getByRole('link', { name: 'San Jose, CA, USA' }),
    ).toBeVisible();
    await expect(page.getByText('Rookie Year: 2001')).toBeVisible();
  });

  test('mobile: Stats summary', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      'Team 604 was 58-10-1 in official play and 78-21-1 overall in 2024.',
    );
  });
});
