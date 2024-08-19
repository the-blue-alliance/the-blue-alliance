import { describe, expect, test } from 'vitest';

import { removeNonNumeric, slugify } from './utils';

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
