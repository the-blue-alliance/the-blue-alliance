import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/districts.{-$year}';

const queryClient = {
  ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
} as unknown as QueryClient;

function load(year: string | undefined) {
  return runLoader(Route, {
    params: { year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('districts route loader', () => {
  test('loads the requested year', async () => {
    await expect(load('2019')).resolves.toEqual({ year: 2019 });
  });

  test('throws not-found for a non-numeric year', async () => {
    await expect(load('abc')).rejects.toMatchObject({ isNotFound: true });
  });
});

describe('districts route head', () => {
  test('titles the page with the year', () => {
    expect(runHead(Route, { loaderData: { year: 2019 } })?.meta?.[0]).toEqual({
      title: '2019 FIRST Robotics Districts - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'FIRST Robotics Districts - The Blue Alliance',
    });
  });
});
