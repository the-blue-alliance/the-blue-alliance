import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/suggest.match.video';

function load(match_key: string, match: Promise<unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id === 'getMatch' ? match : Promise.resolve({}),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    deps: { match_key },
    context: { queryClient },
  });
}

describe('suggest match video route', () => {
  test('passes the validated search through as loader deps', () => {
    expect(
      Route.options.loaderDeps?.({
        search: { match_key: '2024mil_f1m2' },
      } as never),
    ).toEqual({ match_key: '2024mil_f1m2' });
  });

  test('loads a valid match key', async () => {
    await expect(
      load('2024mil_f1m2', Promise.resolve({})),
    ).resolves.toBeUndefined();
  });

  test('throws not-found for an invalid match key', async () => {
    await expect(load('2024mil', Promise.resolve({}))).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the match fails to load', async () => {
    await expect(
      load('2024mil_f1m2', Promise.reject(new Error('404'))),
    ).rejects.toMatchObject({ isNotFound: true });
  });
});
