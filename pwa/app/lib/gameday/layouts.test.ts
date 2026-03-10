import { describe, expect, test } from 'vitest';

import { Layout, getBestLayoutForCount } from '~/lib/gameday/layouts';

describe.concurrent('getBestLayoutForCount', () => {
  test('returns single view for 0 or 1 webcasts', () => {
    expect(getBestLayoutForCount(0)).toBe(Layout.SINGLE_VIEW);
    expect(getBestLayoutForCount(1)).toBe(Layout.SINGLE_VIEW);
  });

  test('returns vertical split for 2 webcasts', () => {
    expect(getBestLayoutForCount(2)).toBe(Layout.VERTICAL_SPLIT);
  });

  test('returns 1+2 view for 3 webcasts', () => {
    expect(getBestLayoutForCount(3)).toBe(Layout.ONE_PLUS_TWO);
  });

  test('returns quad view for 4 webcasts', () => {
    expect(getBestLayoutForCount(4)).toBe(Layout.QUAD_VIEW);
  });

  test('returns 1+4 view for 5 webcasts', () => {
    expect(getBestLayoutForCount(5)).toBe(Layout.ONE_PLUS_FOUR);
  });

  test('returns hex view for 6 webcasts', () => {
    expect(getBestLayoutForCount(6)).toBe(Layout.HEX_VIEW);
  });

  test('returns octo-view for 7 or 8 webcasts', () => {
    expect(getBestLayoutForCount(7)).toBe(Layout.OCTO_VIEW);
    expect(getBestLayoutForCount(8)).toBe(Layout.OCTO_VIEW);
  });

  test('returns nona-view for 9+ webcasts', () => {
    expect(getBestLayoutForCount(9)).toBe(Layout.NONA_VIEW);
    expect(getBestLayoutForCount(100)).toBe(Layout.NONA_VIEW);
  });
});
