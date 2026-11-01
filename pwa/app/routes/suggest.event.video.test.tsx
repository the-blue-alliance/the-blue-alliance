import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/suggest.event.video';

function load(event_key: string, event: Promise<unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<() => Promise<unknown>>(() => event),
  } as unknown as QueryClient;
  return runLoader(Route, {
    deps: { event_key },
    context: { queryClient },
  });
}

describe('suggest event video route', () => {
  test('passes the validated search through as loader deps', () => {
    expect(
      Route.options.loaderDeps?.({
        search: { event_key: '2024mil' },
      } as never),
    ).toEqual({ event_key: '2024mil' });
  });

  test('loads a valid event key', async () => {
    await expect(load('2024mil', Promise.resolve({}))).resolves.toBeUndefined();
  });

  test('throws not-found for an invalid event key', async () => {
    await expect(load('mil', Promise.resolve({}))).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the event fails to load', async () => {
    await expect(
      load('2024mil', Promise.reject(new Error('404'))),
    ).rejects.toMatchObject({ isNotFound: true });
  });
});
