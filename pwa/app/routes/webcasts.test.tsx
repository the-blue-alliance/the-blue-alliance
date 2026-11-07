import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/webcasts';

describe('webcasts route', () => {
  test('loads the current season and the date to render with', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-11-07T12:00:00Z'));
    const queryClient = {
      ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue([]),
    } as unknown as QueryClient;

    await expect(
      runLoader(Route, {
        context: { queryClient, currentSeason: 2026 },
      }),
    ).resolves.toEqual({
      year: 2026,
      today: '2026-11-07',
    });
    vi.useRealTimers();
  });

  test('titles the page Live Webcasts', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Live Webcasts - The Blue Alliance',
    });
  });
});
