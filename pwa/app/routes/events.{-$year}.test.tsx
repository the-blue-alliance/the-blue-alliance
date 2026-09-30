import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route as DistrictEventsRoute } from '~/routes/events.$districtAbbreviation.$year';
import { Route } from '~/routes/events.{-$year}';

const queryClient = {
  ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
} as unknown as QueryClient;

function load(year: string | undefined) {
  return runLoader(Route, {
    params: { year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('events route beforeLoad', () => {
  test('redirects a district abbreviation to the district page', () => {
    expect(() =>
      Route.options.beforeLoad?.({ params: { year: 'ne' } } as never),
    ).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/district/$districtAbbreviation/{-$year}',
          params: { districtAbbreviation: 'ne' },
        }),
      }),
    );
  });

  test('lets a numeric year through', () => {
    expect(
      Route.options.beforeLoad?.({ params: { year: '2024' } } as never),
    ).toBeUndefined();
  });
});

describe('events route loader', () => {
  test('defaults to the current season', async () => {
    await expect(load(undefined)).resolves.toEqual({ year: 2026 });
  });

  test('throws not-found for a non-positive year', async () => {
    await expect(load('0')).rejects.toMatchObject({ isNotFound: true });
  });
});

describe('events route head', () => {
  test('titles the page with the year', () => {
    expect(runHead(Route, { loaderData: { year: 2024 } })?.meta?.[0]).toEqual({
      title: '2024 FIRST Robotics Events - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'FIRST Robotics Events - The Blue Alliance',
    });
  });
});

describe('district events route', () => {
  test('redirects to the district page for that year', () => {
    expect(() =>
      DistrictEventsRoute.options.beforeLoad?.({
        params: { districtAbbreviation: 'ne', year: '2024' },
      } as never),
    ).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/district/$districtAbbreviation/{-$year}',
          params: { districtAbbreviation: 'ne', year: '2024' },
        }),
      }),
    );
  });
});
