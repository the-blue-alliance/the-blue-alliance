import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/district.$districtAbbreviation.{-$year}';

const history = [
  { abbreviation: 'ne', display_name: 'NE FIRST', year: 2019 },
  { abbreviation: 'ne', display_name: 'New England', year: 2024 },
];

const activeRanking = {
  team_key: 'frc195',
  point_total: 50,
  event_points: [{ total: 50 }],
};

const teams = [{ key: 'frc195' }, { key: 'frc2168' }];

function load(responses: Record<string, unknown>, year: string | undefined) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id in responses
        ? Promise.resolve(responses[queryKey[0]._id])
        : Promise.reject(new Error('500')),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { districtAbbreviation: 'ne', year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('district route loader', () => {
  test('throws not-found for an invalid year', async () => {
    await expect(load({}, 'abc')).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found when the district history fails to load', async () => {
    await expect(load({}, '2024')).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found for a district with no history', async () => {
    await expect(
      load({ getDistrictHistory: [] }, '2024'),
    ).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('falls back to empty data when the per-year fetches fail', async () => {
    await expect(
      load({ getDistrictHistory: history }, undefined),
    ).resolves.toEqual({
      abbreviation: 'ne',
      currentSeason: 2026,
      year: 2026,
      districtHistory: history,
      rankings: null,
      teams: [],
      events: [],
      awards: [],
      advancementCutoffs: null,
    });
  });

  test('drops rankings for teams with no points this year', async () => {
    const result = await load(
      {
        getDistrictHistory: history,
        getDistrictRankings: [
          activeRanking,
          { team_key: 'frc2168', point_total: 0, event_points: [] },
          { team_key: 'frc177', point_total: 10 },
        ],
      },
      '2024',
    );
    expect(result?.rankings).toEqual([activeRanking]);
  });

  test('keeps only ranked teams once the season is over', async () => {
    const result = await load(
      {
        getDistrictHistory: history,
        getDistrictRankings: [activeRanking],
        getDistrictTeams: teams,
        getDistrictEvents: [{ end_date: '2024-04-01' }],
      },
      '2024',
    );
    expect(result?.teams).toEqual([{ key: 'frc195' }]);
  });

  test('keeps every team while the season is in progress', async () => {
    const result = await load(
      {
        getDistrictHistory: history,
        getDistrictRankings: [activeRanking],
        getDistrictTeams: teams,
        getDistrictEvents: [{ end_date: '2999-04-01' }],
      },
      '2024',
    );
    expect(result?.teams).toEqual(teams);
  });

  test('returns the advancement cutoffs', async () => {
    const result = await load(
      {
        getDistrictHistory: history,
        getDistrictAdvancement: { cutoffs: { dcmp: 40 } },
      },
      '2024',
    );
    expect(result?.advancementCutoffs).toEqual({ dcmp: 40 });
  });
});

describe('district route head', () => {
  test('titles the page with the year and latest district name', () => {
    expect(
      runHead(Route, {
        loaderData: { year: 2024, districtHistory: history },
      })?.meta?.[0],
    ).toEqual({ title: '2024 New England District - The Blue Alliance' });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'The Blue Alliance',
    });
  });
});
