import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runValidateSearch } from '~/routes/-testUtils';
import { Route } from '~/routes/search';

const searchIndex = {
  teams: [{ key: 'frc604', nickname: 'Quixilver' }],
  events: [{ key: '2024casj', name: 'Silicon Valley Regional' }],
};

function beforeLoad(q: string | number) {
  const queryClient = {
    ensureQueryData: vi
      .fn<() => Promise<unknown>>()
      .mockResolvedValue(searchIndex),
  } as unknown as QueryClient;
  return Route.options.beforeLoad?.({
    context: { queryClient },
    search: { q },
  } as never);
}

describe('search route beforeLoad', () => {
  test('redirects a team number query to the team page', async () => {
    await expect(beforeLoad(604)).rejects.toMatchObject({
      options: { to: '/team/604' },
    });
  });

  test('redirects an event key query to the event page', async () => {
    await expect(beforeLoad('2024casj')).rejects.toMatchObject({
      options: { to: '/event/2024casj' },
    });
  });

  test('passes an unmatched query through to the page', async () => {
    await expect(beforeLoad('zzzzqqq')).resolves.toEqual({ query: 'zzzzqqq' });
  });
});

describe('search route', () => {
  test('defaults a missing query to an empty string', () => {
    expect(runValidateSearch(Route, {})).toEqual({ q: '' });
  });

  test('titles the page Search', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Search - The Blue Alliance',
    });
  });
});
