import { describe, expect, test } from 'vitest';

import { RequestResult } from '~/api/tba/read/client';
import { ApiError } from '~/lib/apiError';
import {
  camelCaseToHumanReadable,
  hasAnyMatches,
  median,
  parseParamsForYearElseDefault,
  queryFromAPI,
  removeNonNumeric,
  seasonFromKey,
  seasonFromPath,
  slugify,
  splitIntoNChunks,
} from '~/lib/utils';

describe.concurrent('queryFromAPI', () => {
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

describe.concurrent('parseParamsForYearElseDefault', () => {
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

describe.concurrent('removeNonNumeric', () => {
  test('basic', () => {
    expect(removeNonNumeric('frc604')).toEqual('604');
  });
});

describe.concurrent('slugify', () => {
  test('basic', () => {
    expect(slugify('Week 1')).toEqual('week-1');
    expect(slugify('FIRST Championship - Houston')).toEqual(
      'first-championship-houston',
    );
  });
});

describe.concurrent('median', () => {
  test('basic', () => {
    expect(median([1, 2, 3, 4, 5])).toEqual(3);
    expect(median([1, 2, 3, 4, 5, 6])).toEqual(3.5);
    expect(median([1, 2, 3, 4, 5, 6, 7])).toEqual(4);
  });
});

describe.concurrent('camelCaseToHumanReadable', () => {
  test('basic', () => {
    expect(camelCaseToHumanReadable('camelCaseString')).toEqual(
      'Camel Case String',
    );
    expect(camelCaseToHumanReadable('totalPoints')).toEqual('Total Points');
    expect(camelCaseToHumanReadable('rp')).toEqual('Rp');
  });
});

describe.concurrent('splitIntoNChunks', () => {
  test('basic', () => {
    expect(splitIntoNChunks([1, 2, 3, 4, 5], 2)).toEqual([
      [1, 2, 3],
      [4, 5],
    ]);
  });
});

describe.concurrent('hasAnyMatches', () => {
  test('returns true when any value is nonzero', () => {
    expect(hasAnyMatches({ wins: 1, losses: 0, ties: 0 })).toEqual(true);
    expect(hasAnyMatches({ wins: 0, losses: 2, ties: 0 })).toEqual(true);
    expect(hasAnyMatches({ wins: 0, losses: 0, ties: 3 })).toEqual(true);
  });

  test('returns false for an empty record', () => {
    expect(hasAnyMatches({ wins: 0, losses: 0, ties: 0 })).toEqual(false);
  });
});

describe.concurrent('seasonFromKey', () => {
  test('reads the year prefix off event and match keys', () => {
    expect(seasonFromKey('2024casj')).toEqual(2024);
    expect(seasonFromKey('2024mil_f1m2')).toEqual(2024);
    expect(seasonFromKey('1999flor')).toEqual(1999);
    expect(seasonFromKey('2024')).toEqual(2024);
  });

  test('does not mistake a team key for a season', () => {
    expect(seasonFromKey('frc2024')).toBeUndefined();
    expect(seasonFromKey('frc254')).toBeUndefined();
  });

  test('returns undefined when there is no year', () => {
    expect(seasonFromKey(undefined)).toBeUndefined();
    expect(seasonFromKey('')).toBeUndefined();
    expect(seasonFromKey('status')).toBeUndefined();
    expect(seasonFromKey('3024casj')).toBeUndefined();
  });
});

describe.concurrent('seasonFromPath', () => {
  test('finds the season segment in API paths', () => {
    expect(seasonFromPath('/api/v3/event/2024casj')).toEqual(2024);
    expect(seasonFromPath('/api/v3/match/2024mil_f1m2')).toEqual(2024);
    expect(seasonFromPath('/api/v3/team/frc254/2019')).toEqual(2019);
    expect(seasonFromPath('/api/v3/events/2015')).toEqual(2015);
    expect(seasonFromPath('/api/v3/district/2024fim/events')).toEqual(2024);
  });

  test('skips team numbers that look like years', () => {
    expect(seasonFromPath('/api/v3/team/frc2024')).toBeUndefined();
    expect(seasonFromPath('/api/v3/team/frc2024/2019')).toEqual(2019);
  });

  test('returns undefined for season-less paths', () => {
    expect(seasonFromPath('/api/v3/status')).toBeUndefined();
    expect(seasonFromPath('/api/v3/team/frc254/history')).toBeUndefined();
  });
});
