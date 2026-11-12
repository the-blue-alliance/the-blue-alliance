import { waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { listFavorites } from '~/api/tba/mobile/sdk.gen';
import type { TeamSimple } from '~/api/tba/read';
import { getTeamSimple } from '~/api/tba/read/sdk.gen';
import {
  useFavoriteTeamKeys,
  useFavoriteTeams,
} from '~/lib/hooks/useFavoriteTeams';
import { MODEL_TYPE } from '~/lib/utils';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderHookWithClient } from '~/test/render';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

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

function mockTeam(teamNumber: number) {
  return mockTbaApi(
    getTeamSimple,
    { path: { team_key: `frc${teamNumber}` } },
    team(teamNumber),
  );
}

describe('useFavoriteTeams', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('does not fetch favorites when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const requests = mockTbaApi(listFavorites, {}, { favorites: [] });

    const { result } = renderHookWithClient(() => useFavoriteTeams());

    expect(result.current).toEqual({ favoriteTeams: [], isLoading: false });
    expect(requests).toEqual([]);
  });

  test('loads favorited teams sorted by number, skipping failures and other models', async () => {
    const favoritesRequests = mockTbaApi(
      listFavorites,
      {},
      {
        favorites: [
          { model_key: 'frc604', model_type: MODEL_TYPE.TEAM },
          { model_key: '2026casj', model_type: MODEL_TYPE.EVENT },
          { model_key: 'frc254', model_type: MODEL_TYPE.TEAM },
          { model_key: 'frc9999', model_type: MODEL_TYPE.TEAM },
        ],
      },
    );
    mockTeam(254);
    mockTeam(604);
    mockTbaApiWith(
      getTeamSimple,
      { path: { team_key: 'frc9999' } },
      () => new HttpResponse(null, { status: 404 }),
    );
    const eventAsTeamRequests = mockTbaApi(
      getTeamSimple,
      { path: { team_key: '2026casj' } },
      team(0),
    );

    const { result } = renderHookWithClient(() => useFavoriteTeams());

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(favoritesRequests[0].headers.get('Authorization')).toBe(
      'Bearer token-1',
    );
    expect(result.current.favoriteTeams.map((t) => t.key)).toEqual([
      'frc254',
      'frc604',
    ]);
    expect(eventAsTeamRequests).toEqual([]);
  });

  test('treats a missing favorites list as empty', async () => {
    mockTbaApi(listFavorites, {}, {});

    const { result } = renderHookWithClient(() => useFavoriteTeams());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.favoriteTeams).toEqual([]);
  });

  test('returns no teams when the favorites request fails', async () => {
    mockTbaApiWith(
      listFavorites,
      {},
      () => new HttpResponse(null, { status: 500 }),
    );

    const { result } = renderHookWithClient(() => useFavoriteTeams());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.favoriteTeams).toEqual([]);
  });
});

describe('useFavoriteTeamKeys', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('returns only favorited team keys', async () => {
    mockTbaApi(
      listFavorites,
      {},
      {
        favorites: [
          { model_key: 'frc604', model_type: MODEL_TYPE.TEAM },
          { model_key: '2026casj', model_type: MODEL_TYPE.EVENT },
          { model_key: 'frc254', model_type: MODEL_TYPE.TEAM },
        ],
      },
    );

    const { result } = renderHookWithClient(() => useFavoriteTeamKeys());

    await waitFor(() =>
      expect(result.current.teamKeys).toEqual(['frc604', 'frc254']),
    );
  });

  test('returns no team keys when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = renderHookWithClient(() => useFavoriteTeamKeys());

    expect(result.current.teamKeys).toEqual([]);
  });
});
