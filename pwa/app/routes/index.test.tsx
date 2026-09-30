import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/index';

describe('home route loader', () => {
  test('prefetches the current season events', async () => {
    const ensureQueryData = vi
      .fn<() => Promise<unknown>>()
      .mockResolvedValue([]);
    const queryClient = { ensureQueryData } as unknown as QueryClient;

    await runLoader(Route, {
      context: { queryClient, currentSeason: 2026 },
    });

    expect(ensureQueryData).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: [expect.objectContaining({ path: { year: 2026 } })],
      }),
    );
  });
});
