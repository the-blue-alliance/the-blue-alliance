import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { TeamSimple } from '~/api/tba/read';
import FavoriteTeamsSection from '~/components/tba/favoriteTeamsSection';

const { useFavoriteTeamsMock } = vi.hoisted(() => ({
  useFavoriteTeamsMock:
    vi.fn<() => { favoriteTeams: TeamSimple[]; isLoading: boolean }>(),
}));

vi.mock('~/lib/hooks/useFavoriteTeams', () => ({
  useFavoriteTeams: useFavoriteTeamsMock,
}));

vi.mock('~/components/tba/teamListTable', () => ({
  default: ({ teams }: { teams: TeamSimple[] }) => (
    <ul>
      {teams.map((t) => (
        <li key={t.key}>{t.key}</li>
      ))}
    </ul>
  ),
}));

const team: TeamSimple = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  name: 'NASA',
  city: null,
  state_prov: null,
  country: null,
};

describe('FavoriteTeamsSection', () => {
  beforeEach(() => {
    useFavoriteTeamsMock.mockReturnValue({
      favoriteTeams: [team],
      isLoading: false,
    });
  });

  test('renders favorite teams', () => {
    render(<FavoriteTeamsSection />);
    expect(
      screen.getByRole('heading', { name: 'Favorite Teams' }),
    ).toBeTruthy();
    expect(screen.getByText('frc254')).toBeTruthy();
  });

  test('renders nothing while loading', () => {
    useFavoriteTeamsMock.mockReturnValue({
      favoriteTeams: [team],
      isLoading: true,
    });
    const { container } = render(<FavoriteTeamsSection />);
    expect(container.innerHTML).toBe('');
  });

  test('renders nothing without favorites', () => {
    useFavoriteTeamsMock.mockReturnValue({
      favoriteTeams: [],
      isLoading: false,
    });
    const { container } = render(<FavoriteTeamsSection />);
    expect(container.innerHTML).toBe('');
  });
});
