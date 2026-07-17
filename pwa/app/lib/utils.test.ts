import { describe, expect, test } from 'vitest';

import {
  camelCaseToHumanReadable,
  hasAnyMatches,
  median,
  parseParamsForYearElseDefault,
  removeNonNumeric,
  slugify,
  splitIntoNChunks,
} from '~/lib/utils';

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
