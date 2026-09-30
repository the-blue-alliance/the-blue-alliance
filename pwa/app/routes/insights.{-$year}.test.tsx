import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/insights.{-$year}';

interface QueryOptions {
  queryKey: [{ _id: string; path: { year: number } }];
}

function leaderboard(keyType: string, keys: unknown[]) {
  return {
    category: 'leaderboard',
    data: { key_type: keyType, rankings: [{ keys, value: 1 }] },
  };
}

function load(year: string | undefined, insights: unknown[]) {
  const ensureQueryData = vi.fn<(options: QueryOptions) => Promise<unknown>>(
    ({ queryKey }) =>
      Promise.resolve(queryKey[0]._id === 'getInsightsV2Year' ? insights : []),
  );
  const queryClient = { ensureQueryData } as unknown as QueryClient;
  const result = runLoader(Route, {
    params: { year },
    context: { queryClient },
  });
  return { result, ensureQueryData };
}

describe('insights route loader', () => {
  test('loads overall insights when no year is given', async () => {
    const { result } = load(undefined, [{ category: 'streak' }]);
    await expect(result).resolves.toMatchObject({ year: 0 });
  });

  test('treats an empty year as overall insights', async () => {
    const { result } = load('', [{ category: 'streak' }]);
    await expect(result).resolves.toMatchObject({ year: 0 });
  });

  test('throws not-found for a non-numeric year', async () => {
    await expect(load('abc', []).result).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found for year zero', async () => {
    await expect(load('0', []).result).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the year has no insights', async () => {
    await expect(load('2024', []).result).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('groups insights by category and drops clubs', async () => {
    const insights = [
      leaderboard('team', ['frc254']),
      { category: 'streak' },
      { category: 'timeseries' },
      { category: 'game_stats' },
      { category: 'clubs' },
    ];
    await expect(load('2024', insights).result).resolves.toEqual({
      year: 2024,
      eventYears: [],
      leaderboards: [insights[0]],
      streaks: [insights[1]],
      timeseries: [insights[2]],
      successRates: [insights[3]],
    });
  });

  test('collects the years of events named in event leaderboards', async () => {
    const insights = [leaderboard('event', ['2019casj', '2017casj'])];
    await expect(load(undefined, insights).result).resolves.toMatchObject({
      eventYears: [2017, 2019],
    });
  });

  test('collects the years of events behind match leaderboard keys', async () => {
    const insights = [leaderboard('match', ['2018casj_qm1', 'not-a-match'])];
    await expect(load(undefined, insights).result).resolves.toMatchObject({
      eventYears: [2018],
    });
  });

  test('ignores non-string leaderboard keys', async () => {
    const insights = [leaderboard('event', [['2019casj']])];
    await expect(load(undefined, insights).result).resolves.toMatchObject({
      eventYears: [],
    });
  });

  test('prefetches events for each leaderboard year', async () => {
    const { result, ensureQueryData } = load(undefined, [
      leaderboard('event', ['2019casj']),
    ]);
    await result;
    expect(ensureQueryData).toHaveBeenLastCalledWith(
      expect.objectContaining({
        queryKey: [expect.objectContaining({ path: { year: 2019 } })],
      }),
    );
  });
});

describe('insights route head', () => {
  test('titles a season page with its year', () => {
    expect(runHead(Route, { loaderData: { year: 2024 } })?.meta?.[0]).toEqual({
      title: '2024 Insights - The Blue Alliance',
    });
  });

  test('titles the all-time page Overall', () => {
    expect(runHead(Route, { loaderData: { year: 0 } })?.meta?.[0]).toEqual({
      title: 'Overall Insights - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Insights - The Blue Alliance',
    });
  });
});
