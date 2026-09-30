import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runLoader, runValidateSearch } from '~/routes/-testUtils';
import { Route } from '~/routes/suggest.team.media';

function load(team_key: string) {
  const queryClient = {
    ensureQueryData: vi.fn<() => Promise<unknown>>().mockResolvedValue({}),
  } as unknown as QueryClient;
  return runLoader(Route, {
    deps: { team_key, year: 2024 },
    context: { queryClient },
  });
}

describe('suggest team media route', () => {
  test('passes the validated search through as loader deps', () => {
    expect(
      Route.options.loaderDeps?.({
        search: { team_key: 'frc254', year: 2024 },
      } as never),
    ).toEqual({ team_key: 'frc254', year: 2024 });
  });

  test('loads a valid team key', async () => {
    await expect(load('frc254')).resolves.toBeUndefined();
  });

  test('throws not-found for an invalid team key', async () => {
    await expect(load('254')).rejects.toMatchObject({ isNotFound: true });
  });

  test('replaces a malformed year with 0', () => {
    expect(runValidateSearch(Route, { team_key: 'frc254', year: 'x' })).toEqual(
      { team_key: 'frc254', year: 0 },
    );
  });
});
