import { describe, expect, test } from 'vitest';

import { resolveShortKey } from '~/lib/shortUrl';

describe('resolveShortKey', () => {
  test.each([
    ['a team number', '254', { type: 'team', teamNumber: '254' }],
    [
      'a team number with leading zeros',
      '00254',
      { type: 'team', teamNumber: '254' },
    ],
    [
      'a five-digit team number',
      '99999',
      { type: 'team', teamNumber: '99999' },
    ],
    ['a four-digit number', '2024', { type: 'team', teamNumber: '2024' }],
    ['an event key', '2024miket', { type: 'event', eventKey: '2024miket' }],
    [
      'an event key ending in a digit',
      '2024cmp2',
      { type: 'event', eventKey: '2024cmp2' },
    ],
    ['an unknown suffix', '2024xyz', { type: 'event', eventKey: '2024xyz' }],
    [
      'a district key',
      '2024fim',
      { type: 'district', abbreviation: 'fim', year: '2024' },
    ],
    [
      'an old district key',
      '2019mar',
      { type: 'district', abbreviation: 'mar', year: '2019' },
    ],
    [
      'a two-letter district key',
      '2023ne',
      { type: 'district', abbreviation: 'ne', year: '2023' },
    ],
  ])('resolves %s', (_name, key, expected) => {
    expect(resolveShortKey(key)).toEqual(expected);
  });

  test.each([
    ['text', 'abc'],
    ['a six-digit number', '123456'],
    ['a year without a suffix', '2024-'],
    ['an uppercase event key', '2024MIKET'],
    ['an empty key', ''],
  ])('returns null for %s', (_name, key) => {
    expect(resolveShortKey(key)).toBeNull();
  });
});
