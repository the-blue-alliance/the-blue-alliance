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
  });

  test('Event sections', async ({ page }) => {
    await expect(
      page.getByRole('link', { name: 'Silicon Valley Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Sacramento Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Monterey Bay Regional' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Milstein Division' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Einstein Field' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Sunset Showdown' }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'Chezy Champs' }),
    ).toBeVisible();
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
      page.locator('_react=InlineIcon').nth(0).getByRole('link'),
    ).toHaveText('San Jose, California, USA');
    await expect(page.locator('_react=Accordion')).toContainText(
      'Leland High School',
    );
    await expect(page.locator('_react=InlineIcon').nth(2)).toHaveText(
      'Rookie Year: 2001',
    );
    await expect(page.locator('_react=InlineIcon').nth(3)).toHaveText(
      'Details on FRC Events',
    );
    await expect(page.locator('_react=InlineIcon').nth(4)).toHaveText(
      'Statbotics',
    );
  });
});
