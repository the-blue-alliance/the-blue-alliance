import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/events.regional.{-$year}';

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
    params: { year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('regional rankings route loader', () => {
  test('throws not-found for a year before the regional pool', async () => {
    await expect(
      load({ getRegionalRankings: [] }, '2024'),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found for an invalid year', async () => {
    await expect(load({}, 'abc')).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found when the rankings fail to load', async () => {
    await expect(load({}, '2025')).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the rankings are null', async () => {
    await expect(
      load({ getRegionalRankings: null }, '2025'),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('defaults to the current season', async () => {
    await expect(
      load({ getRegionalRankings: [] }, undefined),
    ).resolves.toMatchObject({ year: 2026 });
  });

  test('falls back to null advancement when it fails to load', async () => {
    await expect(
      load({ getRegionalRankings: [] }, '2025'),
    ).resolves.toMatchObject({ advancement: null });
  });

  test('names events by short name, falling back to the full name', async () => {
    const result = await load(
      {
        getRegionalRankings: [],
        getEventsByYear: [
          {
            key: '2025camb',
            short_name: 'Pinnacles',
            name: 'Pinnacles Regional',
          },
          { key: '2025cada', short_name: null, name: 'Sacramento Regional' },
        ],
      },
      '2025',
    );

    expect(result.eventNames).toEqual({
      '2025camb': 'Pinnacles',
      '2025cada': 'Sacramento Regional',
    });
  });
});

describe('regional rankings route head', () => {
  test('titles the page with the year', () => {
    expect(runHead(Route, { loaderData: { year: 2025 } })?.meta?.[0]).toEqual({
      title: '2025 Regional Championship Pool Rankings - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Regional Championship Pool Rankings - The Blue Alliance',
    });
  });
});
