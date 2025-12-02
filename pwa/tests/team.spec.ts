import { expect, test } from '@playwright/test';

test.describe('/team/604/2024', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/team/604/2024');
  });

  test('Event sidebar', async ({ page }) => {
    await expect(
      page.locator('li').filter({ hasText: 'Silicon Valley' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Sacramento' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Monterey Bay' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Milstein' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Einstein' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Sunset Showdown' }),
    ).toBeVisible();
    await expect(
      page.locator('li').filter({ hasText: 'Chezy Champs' }),
    ).toBeVisible();
  });

  test('Event sections', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Silicon Valley Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Silicon Valley Regional' }),
    ).toHaveAttribute('href', '/event/2024casj');

    await expect(
      page.getByRole('link', { name: 'Sacramento Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Sacramento Regional' }),
    ).toHaveAttribute('href', '/event/2024cada');

    await expect(
      page.getByRole('link', { name: 'Monterey Bay Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Monterey Bay Regional' }),
    ).toHaveAttribute('href', '/event/2024camb');

    await expect(
      page.getByRole('link', { name: 'Milstein Division' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Milstein Division' }),
    ).toHaveAttribute('href', '/event/2024mil');

    await expect(
      page.getByRole('link', { name: 'Einstein Field' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Einstein Field' }),
    ).toHaveAttribute('href', '/event/2024cmptx');

    await expect(
      page.getByRole('heading', { name: 'Sunset Showdown' }).getByRole('link'),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Sunset Showdown' }).getByRole('link'),
    ).toHaveAttribute('href', '/event/2024sunshow');

    await expect(
      page.getByRole('heading', { name: 'Chezy Champs' }).getByRole('link'),
    ).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Chezy Champs' }).getByRole('link'),
    ).toHaveAttribute('href', '/event/2024cc');
  });

  test('Social media', async ({ page }) => {
    const socialMediaLinks = page.locator('_react=TeamSocialMediaList');
    await expect(socialMediaLinks).toHaveCount(5);

    await expect(socialMediaLinks.nth(0)).toHaveText('frc604');
    await expect(socialMediaLinks.nth(0)).toBeVisible();
    await expect(socialMediaLinks.nth(0)).toHaveAttribute(
      'href',
      'https://www.facebook.com/frc604',
    );

    await expect(socialMediaLinks.nth(1)).toHaveText('frc604');
    await expect(socialMediaLinks.nth(1)).toBeVisible();
    await expect(socialMediaLinks.nth(1)).toHaveAttribute(
      'href',
      'https://github.com/frc604',
    );

    await expect(socialMediaLinks.nth(2)).toHaveText('frc604');
    await expect(socialMediaLinks.nth(2)).toBeVisible();
    await expect(socialMediaLinks.nth(2)).toHaveAttribute(
      'href',
      'https://www.instagram.com/frc604',
    );

    await expect(socialMediaLinks.nth(3)).toHaveText('frc604');
    await expect(socialMediaLinks.nth(3)).toBeVisible();
    await expect(socialMediaLinks.nth(3)).toHaveAttribute(
      'href',
      'https://x.com/frc604',
    );

    await expect(socialMediaLinks.nth(4)).toHaveText('@frc604');
    await expect(socialMediaLinks.nth(4)).toBeVisible();
    await expect(socialMediaLinks.nth(4)).toHaveAttribute(
      'href',
      'https://www.youtube.com/@frc604',
    );
  });

  test('Header', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Team 604 - Quixilver');
    await expect(
      page.getByRole('link', { name: 'San Jose, California, USA' }),
    ).toBeVisible();

    await expect(
      page.getByRole('button', { name: 'Leland High School with 16' }),
    ).toBeVisible();

    await expect(page.getByText('Rookie Year: 2001')).toBeVisible();

    await expect(page.getByRole('link', { name: 'FRC Events' })).toBeVisible();

    await expect(page.getByRole('link', { name: 'Statbotics' })).toBeVisible();
  });

  test('Stats', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      'Team 604 was 58-10-1 in official play and 78-21-1 overall in 2024.',
    );

    await page.getByText('Show Details').click();

    await expect(
      page.getByTestId('test_Official Events').locator('dt'),
    ).toHaveText('Official Events');
    await expect(
      page.getByTestId('test_Official Events').locator('dd'),
    ).toHaveText('5');

    await expect(page.getByTestId('official_quals_cell')).toHaveText('38-5-1');
    await page.getByTestId('official_quals_cell').hover();
    await expect(
      page.getByTestId('official_quals_tooltip').first(),
    ).toContainText('86% winrate');

    await expect(page.getByTestId('official_playoff_cell')).toHaveText(
      '20-5-0',
    );
    await page.getByTestId('official_playoff_cell').hover();
    await expect(page.getByTestId('official_playoff_tooltip')).toContainText(
      '80% winrate',
    );

    await expect(page.getByTestId('official_overall_cell')).toHaveText(
      '58-10-1',
    );
    await page.getByTestId('official_overall_cell').hover();
    await expect(
      page.getByTestId('official_overall_tooltip').first(),
    ).toContainText('84% winrate');

    await expect(page.getByTestId('unofficial_quals_cell')).toHaveText(
      '14-6-0',
    );
    await page.getByTestId('unofficial_quals_cell').hover();
    await expect(page.getByTestId('unofficial_quals_tooltip')).toContainText(
      '70% winrate',
    );

    await expect(page.getByTestId('unofficial_playoff_cell')).toHaveText(
      '6-5-0',
    );
    await page.getByTestId('unofficial_playoff_cell').hover();
    await expect(page.getByTestId('unofficial_playoff_tooltip')).toContainText(
      '55% winrate',
    );

    await expect(page.getByTestId('unofficial_overall_cell')).toHaveText(
      '20-11-0',
    );
    await page.getByTestId('unofficial_overall_cell').hover();
    await expect(page.getByTestId('unofficial_overall_tooltip')).toContainText(
      '65% winrate',
    );

    await expect(page.getByTestId('combined_quals_cell')).toHaveText('52-11-1');
    await page.getByTestId('combined_quals_cell').hover();
    await expect(page.getByTestId('combined_quals_tooltip')).toContainText(
      '81% winrate',
    );

    await expect(page.getByTestId('combined_playoff_cell')).toHaveText(
      '26-10-0',
    );
    await page.getByTestId('combined_playoff_cell').hover();
    await expect(page.getByTestId('combined_playoff_tooltip')).toContainText(
      '72% winrate',
    );

    await expect(page.getByTestId('combined_overall_cell')).toHaveText(
      '78-21-1',
    );
    await page.getByTestId('combined_overall_cell').hover();
    await expect(page.getByTestId('combined_overall_tooltip')).toContainText(
      '78% winrate',
    );
  });
});
