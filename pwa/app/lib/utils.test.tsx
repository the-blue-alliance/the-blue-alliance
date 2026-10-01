import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, renderHook, waitFor } from '@testing-library/react';
import { type PropsWithChildren, Suspense } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { RequestResult } from '~/api/tba/read/client';
import { ApiError } from '~/lib/apiError';
import {
  STATE_TO_ABBREVIATION,
  addRecords,
  buildPublicCacheControlHeaders,
  camelCaseToHumanReadable,
  confidence,
  convertMsToDays,
  doThrowNotFound,
  hasAnyMatches,
  hoursToMilliseconds,
  joinComponents,
  median,
  minutesToMilliseconds,
  parseParamsForTeamPgNumElseDefault,
  parseParamsForYearElseDefault,
  pluralize,
  publicCacheControlHeaders,
  queryFromAPI,
  removeNonNumeric,
  secondsToMilliseconds,
  slugify,
  splitIntoNChunks,
  stringifyRecord,
  timestampsAreOnDifferentDays,
  useValidYears,
  winrateFromRecord,
  zip,
} from '~/lib/utils';

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getStatusOptions: () => ({
    queryKey: ['status'],
    queryFn: () => Promise.resolve({ max_season: 1995 }),
  }),
}));

describe('queryFromAPI', () => {
  test('resolves with the response data on success', async () => {
    const apiPromise = Promise.resolve({
      data: 42,
      error: undefined,
      response: new Response(),
    }) as RequestResult<number, unknown, false>;

    await expect(queryFromAPI(apiPromise)).resolves.toEqual(42);
  });

  test('rejects with an ApiError carrying the response status on failure', async () => {
    const apiPromise = Promise.resolve({
      data: undefined,
      error: 'not found',
      response: new Response(null, { status: 404, statusText: 'Not Found' }),
    }) as RequestResult<unknown, unknown, false>;

    const rejection = queryFromAPI(apiPromise);
    await expect(rejection).rejects.toBeInstanceOf(ApiError);
    await expect(rejection).rejects.toMatchObject({
      status: 404,
      message: 'Not Found',
    });
  });
});

describe('parseParamsForYearElseDefault', () => {
  const currentSeason = 2026;

  test('returns currentSeason when no year param is given', () => {
    expect(parseParamsForYearElseDefault(currentSeason, {})).toEqual(
      currentSeason,
    );
  });

  test('parses a valid year param', () => {
    expect(
      parseParamsForYearElseDefault(currentSeason, { year: '2015' }),
    ).toEqual(2015);
  });

  test('returns undefined for a non-numeric year param', () => {
    expect(
      parseParamsForYearElseDefault(currentSeason, { year: 'not-a-year' }),
    ).toBeUndefined();
  });

  test('returns undefined for a non-positive year param', () => {
    expect(
      parseParamsForYearElseDefault(currentSeason, { year: '0' }),
    ).toBeUndefined();
    expect(
      parseParamsForYearElseDefault(currentSeason, { year: '-5' }),
    ).toBeUndefined();
  });
});

describe('removeNonNumeric', () => {
  test('basic', () => {
    expect(removeNonNumeric('frc604')).toEqual('604');
  });
});

describe('slugify', () => {
  test('basic', () => {
    expect(slugify('Week 1')).toEqual('week-1');
    expect(slugify('FIRST Championship - Houston')).toEqual(
      'first-championship-houston',
    );
  });
});

describe('median', () => {
  test('basic', () => {
    expect(median([1, 2, 3, 4, 5])).toEqual(3);
    expect(median([1, 2, 3, 4, 5, 6])).toEqual(3.5);
    expect(median([1, 2, 3, 4, 5, 6, 7])).toEqual(4);
  });
});

describe('camelCaseToHumanReadable', () => {
  test('basic', () => {
    expect(camelCaseToHumanReadable('camelCaseString')).toEqual(
      'Camel Case String',
    );
    expect(camelCaseToHumanReadable('totalPoints')).toEqual('Total Points');
    expect(camelCaseToHumanReadable('rp')).toEqual('Rp');
  });
});

describe('splitIntoNChunks', () => {
  test('basic', () => {
    expect(splitIntoNChunks([1, 2, 3, 4, 5], 2)).toEqual([
      [1, 2, 3],
      [4, 5],
    ]);
  });
});

describe('hasAnyMatches', () => {
  test('returns true when any value is nonzero', () => {
    expect(hasAnyMatches({ wins: 1, losses: 0, ties: 0 })).toEqual(true);
    expect(hasAnyMatches({ wins: 0, losses: 2, ties: 0 })).toEqual(true);
    expect(hasAnyMatches({ wins: 0, losses: 0, ties: 3 })).toEqual(true);
  });

  test('returns false for an empty record', () => {
    expect(hasAnyMatches({ wins: 0, losses: 0, ties: 0 })).toEqual(false);
  });
});

describe('useValidYears', () => {
  function createWrapper() {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return function Wrapper({ children }: PropsWithChildren) {
      return (
        <QueryClientProvider client={queryClient}>
          <Suspense fallback={null}>{children}</Suspense>
        </QueryClientProvider>
      );
    };
  }

  test('lists every season from the latest back to 1992', async () => {
    const { result } = renderHook(() => useValidYears(), {
      wrapper: createWrapper(),
    });

    await waitFor(() =>
      expect(result.current).toEqual([1995, 1994, 1993, 1992]),
    );
  });
});

describe('parseParamsForTeamPgNumElseDefault', () => {
  test('defaults to the first page', () => {
    expect(parseParamsForTeamPgNumElseDefault({}, 10)).toBe(1);
  });

  test('parses a page number within range', () => {
    expect(parseParamsForTeamPgNumElseDefault({ pgNum: '3' }, 10)).toBe(3);
  });

  test('rejects a page number past the last page', () => {
    expect(parseParamsForTeamPgNumElseDefault({ pgNum: '11' }, 10)).toBe(
      undefined,
    );
  });

  test('rejects a non-numeric page', () => {
    expect(parseParamsForTeamPgNumElseDefault({ pgNum: 'abc' }, 10)).toBe(
      undefined,
    );
  });

  test('rejects page zero', () => {
    expect(parseParamsForTeamPgNumElseDefault({ pgNum: '0' }, 10)).toBe(
      undefined,
    );
  });
});

describe('timestampsAreOnDifferentDays', () => {
  test('is false for two times on the same UTC day', () => {
    expect(timestampsAreOnDifferentDays(1704067200, 1704070800, null)).toBe(
      false,
    );
  });

  test('is true across UTC midnight', () => {
    expect(timestampsAreOnDifferentDays(1704063600, 1704067200, 'UTC')).toBe(
      true,
    );
  });

  test('compares days in the given timezone', () => {
    expect(
      timestampsAreOnDifferentDays(
        1704063600,
        1704067200,
        'America/Los_Angeles',
      ),
    ).toBe(false);
  });
});

describe('zip', () => {
  test('pairs elements up to the shortest array', () => {
    expect(zip([1, 2, 3], ['a', 'b'])).toEqual([
      [1, 'a'],
      [2, 'b'],
    ]);
  });

  test('is empty without arrays', () => {
    expect(zip()).toEqual([]);
  });

  test('treats an undefined array as empty', () => {
    expect(zip([1, 2], undefined)).toEqual([]);
  });
});

describe('time conversions', () => {
  test('converts milliseconds to days', () => {
    expect(convertMsToDays(172800000)).toBe(2);
  });

  test('converts seconds to milliseconds', () => {
    expect(secondsToMilliseconds(61)).toBe(61000);
  });

  test('converts minutes to milliseconds', () => {
    expect(minutesToMilliseconds(2)).toBe(120000);
  });

  test('converts hours to milliseconds', () => {
    expect(hoursToMilliseconds(1)).toBe(3600000);
  });
});

describe('records', () => {
  test('stringifies a record as W-L-T', () => {
    expect(stringifyRecord({ wins: 10, losses: 2, ties: 1 })).toBe('10-2-1');
  });

  test('adds two records', () => {
    expect(
      addRecords(
        { wins: 10, losses: 2, ties: 1 },
        { wins: 1, losses: 1, ties: 1 },
      ),
    ).toEqual({ wins: 11, losses: 3, ties: 2 });
  });

  test('computes the win rate over all matches', () => {
    expect(winrateFromRecord({ wins: 3, losses: 1, ties: 0 })).toBe(0.75);
  });

  test('has a zero win rate without matches', () => {
    expect(winrateFromRecord({ wins: 0, losses: 0, ties: 0 })).toBe(0);
  });
});

describe('pluralize', () => {
  test('uses the singular for one', () => {
    expect(pluralize(1, 'match', 'matches')).toBe('1 match');
  });

  test('uses the plural otherwise', () => {
    expect(pluralize(2, 'match', 'matches')).toBe('2 matches');
  });

  test('can omit the number', () => {
    expect(pluralize(0, 'match', 'matches', false)).toBe('matches');
  });
});

describe('joinComponents', () => {
  test('joins components with a string separator', () => {
    const { container } = render(<>{joinComponents(['a', 'b', 'c'], ', ')}</>);

    expect(container.textContent).toBe('a, b, c');
  });

  test('joins components with a node separator', () => {
    const { container } = render(
      <>{joinComponents(['a', 'b'], <span> | </span>)}</>,
    );

    expect(container.textContent).toBe('a | b');
  });
});

describe('STATE_TO_ABBREVIATION', () => {
  test('inverts the abbreviation map', () => {
    expect(STATE_TO_ABBREVIATION.get('California')).toBe('CA');
  });
});

describe('confidence', () => {
  test('is zero without any votes', () => {
    expect(confidence(0, 0)).toBe(0);
  });

  test('scores a perfect record below 1 to account for sample size', () => {
    expect(confidence(10, 0)).toBeCloseTo(0.5263, 4);
  });

  test('ranks a larger sample of the same rate higher', () => {
    expect(confidence(100, 0)).toBeGreaterThan(confidence(10, 0));
  });
});

describe('doThrowNotFound', () => {
  test('throws a router not-found error', () => {
    expect(() => doThrowNotFound()).toThrow(
      expect.objectContaining({ isNotFound: true }),
    );
  });
});

describe('buildPublicCacheControlHeaders', () => {
  test('returns no headers outside production', () => {
    expect(buildPublicCacheControlHeaders()).toEqual({});
  });

  test('sets a public max-age with stale-while-revalidate in production', () => {
    vi.stubEnv('NODE_ENV', 'production');

    expect(buildPublicCacheControlHeaders(30)).toEqual({
      'Cache-Control': 'public, max-age=30, stale-while-revalidate=60',
      'CDN-Cache-Control': 'max-age=30',
    });
  });

  test('defaults to a 61 second max-age', () => {
    vi.stubEnv('NODE_ENV', 'production');

    expect(buildPublicCacheControlHeaders()['CDN-Cache-Control']).toBe(
      'max-age=61',
    );
  });

  test('publicCacheControlHeaders builds the same headers lazily', () => {
    vi.stubEnv('NODE_ENV', 'production');

    expect(publicCacheControlHeaders(30)()).toEqual(
      buildPublicCacheControlHeaders(30),
    );
  });
});

describe('median of nothing', () => {
  test('is undefined for an empty list', () => {
    expect(median([])).toBeUndefined();
  });
});

describe('splitIntoNChunks of nothing', () => {
  test('yields no chunks for an empty list', () => {
    expect(splitIntoNChunks([], 3)).toEqual([]);
  });
});
