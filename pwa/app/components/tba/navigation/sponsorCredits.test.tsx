import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { SponsorsList } from '~/api/tba/read';
import {
  FooterSponsorCredit,
  MobileMenuSponsorCredit,
} from '~/components/tba/navigation/sponsorCredits';

const { sponsorsMock } = vi.hoisted(() => ({
  sponsorsMock: vi.fn<() => Promise<SponsorsList>>(),
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getSponsorsOptions: () => ({
    queryKey: ['sponsors'],
    queryFn: sponsorsMock,
  }),
}));

const andymark = {
  name: 'AndyMark',
  url: 'https://www.andymark.com/',
  logo_style: 'wordmark',
  logo_url:
    'https://www.thebluealliance.com/images/sponsors/andymark-on-light.png',
  logo_url_dark:
    'https://www.thebluealliance.com/images/sponsors/andymark-on-dark.png',
} as const;

const quillfeather = {
  name: 'Quillfeather Robotics',
  url: 'https://quillfeather.example.com/',
  logo_style: 'mark',
  logo_url: 'https://quillfeather.example.com/light.png',
  logo_url_dark: 'https://quillfeather.example.com/dark.png',
} as const;

const plainText = {
  name: 'Plain Text Co',
  url: 'https://plaintext.example.com/',
  logo_style: 'wordmark',
  logo_url: null,
  logo_url_dark: null,
} as const;

function renderWithClient(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

beforeEach(() => {
  sponsorsMock.mockReset();
});

describe('MobileMenuSponsorCredit', () => {
  test('renders nothing when there are no sponsors', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [] });
    const { container } = renderWithClient(
      <MobileMenuSponsorCredit animationDelayMs={0} />,
    );

    await vi.waitFor(() => expect(sponsorsMock).toHaveBeenCalled());
    expect(container.textContent).toBe('');
  });

  test('renders nothing when the request fails', async () => {
    sponsorsMock.mockRejectedValue(new Error('boom'));
    const { container } = renderWithClient(
      <MobileMenuSponsorCredit animationDelayMs={0} />,
    );

    await vi.waitFor(() => expect(sponsorsMock).toHaveBeenCalled());
    expect(container.textContent).toBe('');
  });

  test('uses the singular label for one sponsor', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    expect(
      await screen.findByText('Thanks to our platinum sponsor'),
    ).toBeTruthy();
  });

  test('shows the white logo for a wordmark sponsor', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    expect((await screen.findByAltText('AndyMark')).getAttribute('src')).toBe(
      'https://www.thebluealliance.com/images/sponsors/andymark-on-dark.png',
    );
  });

  test('links a sponsor to its site in a new tab', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    const link = await screen.findByRole('link', { name: 'AndyMark' });
    expect([link.getAttribute('href'), link.getAttribute('target')]).toEqual([
      'https://www.andymark.com/',
      '_blank',
    ]);
  });

  test('uses the plural label for two sponsors', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark, quillfeather] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    expect(
      await screen.findByText('Thanks to our platinum sponsors'),
    ).toBeTruthy();
  });

  test('names a mark sponsor beside its logo', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark, quillfeather] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    const link = await screen.findByRole('link', {
      name: 'Quillfeather Robotics',
    });
    expect(link.querySelector('img')?.getAttribute('src')).toBe(
      'https://quillfeather.example.com/dark.png',
    );
  });

  test('shows an unknown logo style as a wordmark', async () => {
    sponsorsMock.mockResolvedValue({
      sponsors: [{ ...andymark, logo_style: 'banner' }],
    });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    expect(await screen.findByAltText('AndyMark')).toBeTruthy();
  });

  test('names a sponsor without a logo as text', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [plainText] });
    renderWithClient(<MobileMenuSponsorCredit animationDelayMs={0} />);

    const link = await screen.findByRole('link', { name: 'Plain Text Co' });
    expect(link.querySelector('img')).toBeNull();
  });
});

describe('FooterSponsorCredit', () => {
  test('renders nothing when there are no sponsors', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [] });
    const { container } = renderWithClient(<FooterSponsorCredit />);

    await vi.waitFor(() => expect(sponsorsMock).toHaveBeenCalled());
    expect(container.textContent).toBe('');
  });

  test('shows the full-color logo outside dark mode', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark] });
    renderWithClient(<FooterSponsorCredit />);

    const [light] = await screen.findAllByAltText('AndyMark');
    expect(light.getAttribute('src')).toBe(andymark.logo_url);
    expect(light.className).toContain('dark:hidden');
  });

  test('shows the white logo dimmed to the text color in dark mode', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark] });
    renderWithClient(<FooterSponsorCredit />);

    const [, dark] = await screen.findAllByAltText('AndyMark');
    expect(dark.getAttribute('src')).toBe(andymark.logo_url_dark);
    expect(dark.className).toContain('dark:inline');
    expect(dark.className).toContain('brightness-90');
  });

  test('uses one logo when there is no dark variant', async () => {
    sponsorsMock.mockResolvedValue({
      sponsors: [{ ...andymark, logo_url_dark: null }],
    });
    renderWithClient(<FooterSponsorCredit />);

    expect(await screen.findAllByAltText('AndyMark')).toHaveLength(1);
  });

  test('uses the plural label for two sponsors', async () => {
    sponsorsMock.mockResolvedValue({ sponsors: [andymark, quillfeather] });
    renderWithClient(<FooterSponsorCredit />);

    await screen.findByRole('link', { name: 'Quillfeather Robotics' });
    expect(screen.getByText(/Thanks to our platinum sponsors/)).toBeTruthy();
  });
});
