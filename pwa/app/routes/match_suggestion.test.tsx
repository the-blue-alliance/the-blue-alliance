import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/match_suggestion';

describe('match suggestion route loader', () => {
  test('returns no events when the season has none', async () => {
    const queryClient = {
      ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
    } as unknown as QueryClient;

    await expect(
      runLoader(Route, {
        context: { queryClient, currentSeason: 2026 },
      }),
    ).resolves.toEqual({ events: [] });
  });
});
