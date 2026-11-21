import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/suggest.event.media';

function load(event_key: string, event: Promise<unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id === 'getEvent' ? event : Promise.resolve([]),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    deps: { event_key },
    context: { queryClient },
  });
}

describe('suggest event media route', () => {
  test('passes the validated search through as loader deps', () => {
    expect(
      Route.options.loaderDeps?.({
        search: { event_key: '2024casj' },
      } as never),
    ).toEqual({ event_key: '2024casj' });
  });

  test('loads a valid event key', async () => {
    await expect(
      load('2024casj', Promise.resolve({})),
    ).resolves.toBeUndefined();
  });

  test('throws not-found for an invalid event key', async () => {
    await expect(load('casj', Promise.resolve({}))).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the event fails to load', async () => {
    await expect(
      load('2024casj', Promise.reject(new Error('404'))),
    ).rejects.toMatchObject({ isNotFound: true });
  });
});
