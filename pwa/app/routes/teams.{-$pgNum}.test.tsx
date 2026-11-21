import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/teams.{-$pgNum}';

function load(pgNum: string | undefined) {
  const queryClient = {
    ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { pgNum },
    context: { queryClient, status: { max_team_page: 20 } },
  });
}

describe('teams route loader', () => {
  test('defaults to the first page', async () => {
    await expect(load(undefined)).resolves.toEqual({
      pageNum: 1,
      maxPageNum: 11,
    });
  });

  test('throws not-found past the last page', async () => {
    await expect(load('12')).rejects.toMatchObject({
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
