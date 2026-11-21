import { describe, expect, test } from 'vitest';

import { firebaseOnlyQueryFn } from '~/lib/gameday/firebaseQuery';

describe('firebaseOnlyQueryFn', () => {
  test('resolves to no data', () => {
    expect(firebaseOnlyQueryFn()).toBeNull();
  });
});
