import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/hall-of-fame';

describe('hall of fame route', () => {
  test('loads the all-time notables', async () => {
    const notables = [{ name: 'notables_hall_of_fame' }];
    const queryClient = {
      ensureQueryData: vi
        .fn<() => Promise<unknown>>()
        .mockResolvedValue(notables),
    } as unknown as QueryClient;

    await expect(
      runLoader(Route, { context: { queryClient } }),
    ).resolves.toEqual({ notables });
  });

  test('titles the page Hall of Fame', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Hall of Fame - The Blue Alliance',
    });
  });
});
