import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/webcasts';

describe('webcasts route', () => {
  test('loads the current season', async () => {
    const queryClient = {
      ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
    } as unknown as QueryClient;

    await expect(
      runLoader(Route, {
        context: { queryClient, currentSeason: 2026 },
      }),
    ).resolves.toEqual({ year: 2026 });
  });

  test('titles the page Live Webcasts', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Live Webcasts - The Blue Alliance',
    });
  });
});
