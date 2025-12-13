import { describe, expect, test } from 'vitest';

import {
  camelCaseToHumanReadable,
  median,
  removeNonNumeric,
  slugify,
  splitIntoNChunks,
} from '~/lib/utils';

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
