import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/district.$districtAbbreviation.insights';

const history = [
  { abbreviation: 'ne', display_name: 'NE FIRST', year: 2019 },
  { abbreviation: 'ne', display_name: 'New England', year: 2024 },
];

function load(insights: Promise<unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id === 'getDistrictHistory'
        ? Promise.resolve(history)
        : insights,
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { districtAbbreviation: 'ne' },
    context: { queryClient },
  });
}

describe('district insights route loader', () => {
  test('returns the district history', async () => {
    await expect(load(Promise.resolve({}))).resolves.toEqual({
      abbreviation: 'ne',
      history,
    });
  });

  test('throws not-found when the district insights fail to load', async () => {
    await expect(load(Promise.reject(new Error('404')))).rejects.toMatchObject({
      isNotFound: true,
    });
  });
});

describe('district insights route head', () => {
  test('titles the page with the latest district name', () => {
    expect(runHead(Route, { loaderData: { history } })?.meta?.[0]).toEqual({
      title: 'New England District Insights - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'District Insights - The Blue Alliance',
    });
  });
});
