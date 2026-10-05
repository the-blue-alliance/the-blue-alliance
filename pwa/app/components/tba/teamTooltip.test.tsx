import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { type AnchorHTMLAttributes, type ReactNode, Suspense } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { Media, SearchIndex } from '~/api/tba/read';
import {
  TeamLinkWithAvatarTooltip,
  TeamLinkWithTooltip,
  TeamTooltip,
} from '~/components/tba/teamTooltip';

const { searchIndexMock, mediaMock } = vi.hoisted(() => ({
  searchIndexMock: vi.fn<() => Promise<SearchIndex>>(),
  mediaMock: vi.fn<() => Promise<Media[]>>(),
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getSearchIndexOptions: () => ({
    queryKey: ['search-index'],
    queryFn: searchIndexMock,
  }),
  getTeamMediaByYearOptions: ({
    path,
  }: {
    path: { team_key: string; year: number };
  }) => ({
    queryKey: ['team-media', path.team_key, path.year],
    queryFn: mediaMock,
  }),
}));

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({
    children,
    teamOrKey,
    year,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    children?: ReactNode;
    teamOrKey: string;
    year: number;
  }) => (
    <a href={`/team/${teamOrKey.substring(3)}/${year}`} {...props}>
      {children}
    </a>
  ),
}));

const searchIndex: SearchIndex = {
  teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
  events: [],
};

function renderWithClient(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const result = render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback="loading">{ui}</Suspense>
    </QueryClientProvider>,
  );
  return { ...result, queryClient };
}

beforeEach(() => {
  searchIndexMock.mockResolvedValue(searchIndex);
  mediaMock.mockResolvedValue([]);
});

describe('TeamLinkWithTooltip', () => {
  test('renders a plain link when the team is not in the search index', async () => {
    const { container } = renderWithClient(
      <TeamLinkWithTooltip teamKey="frc9999" year={2026} />,
    );
    await screen.findByRole('link', { name: '9999' });
    expect(container.querySelector('a')?.getAttribute('href')).toBe(
      '/team/9999/2026',
    );
  });

  test('renders a winner captain label once the name loads', async () => {
    renderWithClient(
      <TeamLinkWithTooltip teamKey="frc254" year={2026} isWinner isCaptain />,
    );
    const link = await screen.findByRole('link', { name: '254C' });
    expect(link.querySelector('svg')).toBeTruthy();
    expect(link.querySelector('sup')?.textContent).toBe('C');
  });

  test.each([
    [{ disqualified: true }],
    [{ surrogate: true }],
    [{ isWinner: true }],
    [{ isCaptain: true }],
    [{}],
  ])('renders the tooltip trigger with %o', async (props) => {
    const { queryClient } = renderWithClient(
      <TeamLinkWithTooltip teamKey="frc254" year={2026} {...props} />,
    );
    await vi.waitFor(() =>
      expect(queryClient.getQueryData(['search-index'])).toBe(searchIndex),
    );
    const link = await screen.findByRole('link', { name: /^254/ });
    expect(link.getAttribute('href')).toBe('/team/254/2026');
  });
});

describe('TeamTooltip', () => {
  test('renders the nickname, avatar, and status flags', async () => {
    mediaMock.mockResolvedValue([
      {
        type: 'avatar',
        foreign_key: 'avatar_2026_frc254',
        team_keys: ['frc254'],
        details: { base64Image: 'AAAA' },
      } as Media,
    ]);
    renderWithClient(
      <TeamTooltip teamKey="frc254" year={2026} disqualified surrogate />,
    );
    expect(await screen.findByText('The Cheesy Poofs')).toBeTruthy();
    expect(screen.getByRole('img', { name: 'Team Avatar' })).toBeTruthy();
    expect(screen.getByText('Disqualified')).toBeTruthy();
    expect(screen.getByText('Surrogate')).toBeTruthy();
  });

  test('renders without flags', async () => {
    renderWithClient(<TeamTooltip teamKey="frc254" year={2026} />);
    expect(await screen.findByText('The Cheesy Poofs')).toBeTruthy();
    expect(screen.queryByText('Disqualified')).toBeNull();
  });

  test('shows the default avatar for a team without one', async () => {
    renderWithClient(<TeamTooltip teamKey="frc254" year={2026} />);
    expect(
      await screen.findByRole('img', { name: 'Default Team Avatar' }),
    ).toBeTruthy();
  });

  test('renders nothing for an unknown team', async () => {
    const { container } = renderWithClient(
      <TeamTooltip teamKey="frc9999" year={2026} />,
    );
    await screen.findByText('loading');
    await vi.waitFor(() => expect(container.textContent).toBe(''));
  });
});

describe('TeamLinkWithAvatarTooltip', () => {
  test.each([
    [{ isWinner: true, isCaptain: true }, '254C'],
    [{ isWinner: true }, '254'],
    [{ isCaptain: true }, '254C'],
    [{}, '254'],
  ])('renders the label with %o', (props, name) => {
    renderWithClient(
      <TeamLinkWithAvatarTooltip teamKey="frc254" year={2026} {...props} />,
    );
    expect(screen.getByRole('link', { name })).toBeTruthy();
  });
});
