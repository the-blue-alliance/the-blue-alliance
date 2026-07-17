import { dehydrate, hydrate } from '@tanstack/react-query';
import { Temporal } from 'temporal-polyfill';
import { describe, expect, test } from 'vitest';

import { ApiError } from '~/lib/apiError';
import {
  STALE_TIME,
  createQueryClient,
  staleTimeForYear,
} from '~/lib/queryClient';

describe.concurrent('createQueryClient', () => {
  test('defaults staleTime to STALE_TIME.DEFAULT', () => {
    const queryClient = createQueryClient();
    expect(queryClient.getDefaultOptions().queries?.staleTime).toEqual(
      STALE_TIME.DEFAULT,
    );
  });

  test('retry predicate skips 4xx ApiErrors', () => {
    const queryClient = createQueryClient();
    const retry = queryClient.getDefaultOptions().queries?.retry;
    expect(typeof retry).toEqual('function');
    if (typeof retry !== 'function') return;

    expect(retry(0, new ApiError('not found', 404))).toEqual(false);
    expect(retry(0, new ApiError('server error', 500))).toEqual(true);
    expect(retry(2, new ApiError('server error', 500))).toEqual(true);
    expect(retry(3, new ApiError('server error', 500))).toEqual(false);
    expect(retry(0, new Error('network error'))).toEqual(true);
  });

  test('freshly hydrated data is not stale under the default staleTime', () => {
    // Simulates the SSR -> hydration flow: a loader warms the cache on the
    // server, the cache is dehydrated into the payload, and a fresh
    // QueryClient hydrates it on the client. With staleTime: 0 (the old
    // default), this data would be instantly stale and every
    // useSuspenseQuery would refetch on mount. With STALE_TIME.DEFAULT set,
    // it should not be stale immediately after hydration.
    const serverQueryClient = createQueryClient();
    const queryKey = ['test-query'];
    serverQueryClient.setQueryData(queryKey, { hello: 'world' });

    const dehydratedState = dehydrate(serverQueryClient);

    const clientQueryClient = createQueryClient();
    hydrate(clientQueryClient, dehydratedState);

    const query = clientQueryClient.getQueryCache().find({ queryKey });
    expect(query).toBeDefined();
    expect(query?.isStaleByTime(STALE_TIME.DEFAULT)).toEqual(false);
  });
});

describe.concurrent('staleTimeForYear', () => {
  const currentYear = Temporal.Now.plainDateISO().year;

  test('returns HISTORICAL for a past year', () => {
    expect(staleTimeForYear(currentYear - 1)).toEqual(STALE_TIME.HISTORICAL);
    expect(staleTimeForYear(2015)).toEqual(STALE_TIME.HISTORICAL);
  });

  test('returns DEFAULT for the current year', () => {
    expect(staleTimeForYear(currentYear)).toEqual(STALE_TIME.DEFAULT);
  });

  test('returns DEFAULT for a future year', () => {
    expect(staleTimeForYear(currentYear + 1)).toEqual(STALE_TIME.DEFAULT);
  });
});
