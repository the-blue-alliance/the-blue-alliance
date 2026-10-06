import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader, runValidateSearch } from '~/routes/-testUtils';
import { Route } from '~/routes/suggest.team.social_media';

function load(team_key: string) {
  const queryClient = {
    ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue({}),
  } as unknown as QueryClient;
  return runLoader(Route, {
    deps: { team_key },
    context: { queryClient },
  });
}

describe('suggest team social media route', () => {
  test('passes the validated search through as loader deps', () => {
    expect(
      Route.options.loaderDeps?.({
        search: { team_key: 'frc1124' },
      } as never),
    ).toEqual({ team_key: 'frc1124' });
  });

  test('loads a valid team key', async () => {
    await expect(load('frc1124')).resolves.toBeUndefined();
  });

  test('throws not-found for an invalid team key', async () => {
    await expect(load('1124')).rejects.toMatchObject({ isNotFound: true });
  });

  test('replaces a malformed team key with an empty string', () => {
    expect(runValidateSearch(Route, { team_key: 1124 })).toEqual({
      team_key: '',
    });
  });
});
