import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/teams.{-$pgNum}';

function load(pgNum: string | undefined) {
  const ensureQueryData = vi
    .fn<(options: { queryKey: [{ path: object }] }) => Promise<unknown>>()
    .mockResolvedValue([]);
  const queryClient = { ensureQueryData } as unknown as QueryClient;
  const result = runLoader(Route, {
    params: { pgNum },
    context: { queryClient, status: { max_team_page: 20 } },
  });
  return { result, ensureQueryData };
}

describe('teams route loader', () => {
  test('defaults to the first page', async () => {
    await expect(load(undefined).result).resolves.toEqual({
      pageNum: 1,
      maxPageNum: 11,
    });
  });

  test('fetches the two API pages behind a display page', async () => {
    const { result, ensureQueryData } = load('3');
    await result;
    expect(
      ensureQueryData.mock.calls.map(([options]) => options.queryKey[0].path),
    ).toEqual([{ page_num: 4 }, { page_num: 5 }]);
  });

  test('throws not-found past the last page', async () => {
    await expect(load('12').result).rejects.toMatchObject({
      isNotFound: true,
    });
  });
});

describe('teams route head', () => {
  test('titles the page FIRST Robotics Teams', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'FIRST Robotics Teams - The Blue Alliance',
    });
  });
});
