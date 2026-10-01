import { describe, expect, test } from 'vitest';

import { NAV_ITEMS_LIST } from '~/lib/navigation/content';

describe('NAV_ITEMS_LIST', () => {
  test('lists the primary sections in navbar order', () => {
    expect(NAV_ITEMS_LIST.map((item) => item.title)).toEqual([
      'myTBA',
      'Events',
      'Teams',
      'Districts',
      'GameDay',
      'Insights',
    ]);
  });

  test('year-scoped sections link to their current-year route', () => {
    const events = NAV_ITEMS_LIST.find((item) => item.title === 'Events');

    expect(events?.to).toBe('/events/{-$year}');
    expect(events?.params).toEqual({ year: undefined });
  });
});
