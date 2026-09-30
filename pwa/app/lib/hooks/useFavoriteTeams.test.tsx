import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { TeamSimple } from '~/api/tba/read';
import { useFavoriteTeams } from '~/lib/hooks/useFavoriteTeams';
import { MODEL_TYPE } from '~/lib/utils';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
  listFavorites: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
  getTeamSimple: vi.fn<(teamKey: string) => Promise<TeamSimple>>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/api/tba/mobile/sdk.gen', () => ({
  listFavorites: mocks.listFavorites,
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getTeamSimpleOptions: ({ path }: { path: { team_key: string } }) => ({
    queryKey: ['team', path.team_key],
    queryFn: () => mocks.getTeamSimple(path.team_key),
  }),
}));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };

function team(teamNumber: number): TeamSimple {
  return {
    key: `frc${teamNumber}`,
    team_number: teamNumber,
    nickname: `Team ${teamNumber}`,
    name: `Team ${teamNumber}`,
    city: null,
    state_prov: null,
    country: null,
  };
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useFavoriteTeams', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mocks.getTeamSimple.mockImplementation((key) =>
      Promise.resolve(team(Number(key.slice(3)))),
    );
  });

  test('does not fetch favorites when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = renderHook(() => useFavoriteTeams(), {
      wrapper: createWrapper(),
    });

    expect(result.current).toEqual({ favoriteTeams: [], isLoading: false });
    expect(mocks.listFavorites).not.toHaveBeenCalled();
  });

  test('loads favorited teams sorted by number, skipping failures and other models', async () => {
    mocks.listFavorites.mockResolvedValue({
      data: {
        favorites: [
          { model_key: 'frc604', model_type: MODEL_TYPE.TEAM },
          { model_key: '2026casj', model_type: MODEL_TYPE.EVENT },
          { model_key: 'frc254', model_type: MODEL_TYPE.TEAM },
          { model_key: 'frc9999', model_type: MODEL_TYPE.TEAM },
        ],
      },
    });
    mocks.getTeamSimple.mockImplementation((key) =>
      key === 'frc9999'
        ? Promise.reject(new Error('not found'))
        : Promise.resolve(team(Number(key.slice(3)))),
    );

    const { result } = renderHook(() => useFavoriteTeams(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mocks.listFavorites).toHaveBeenCalledWith({ auth: 'token-1' });
    expect(result.current.favoriteTeams.map((t) => t.key)).toEqual([
      'frc254',
      'frc604',
    ]);
    expect(mocks.getTeamSimple).not.toHaveBeenCalledWith('2026casj');
  });

  test('treats a missing favorites list as empty', async () => {
    mocks.listFavorites.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useFavoriteTeams(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.favoriteTeams).toEqual([]);
  });

  test('returns no teams when the favorites request fails', async () => {
    mocks.listFavorites.mockResolvedValue({ data: undefined });

    const { result } = renderHook(() => useFavoriteTeams(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.favoriteTeams).toEqual([]);
    expect(mocks.getTeamSimple).not.toHaveBeenCalled();
  });
});
