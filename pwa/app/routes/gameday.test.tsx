import { describe, expect, test } from 'vitest';

import { runHead, runValidateSearch } from '~/routes/-testUtils';
import { Route as GamedayRoute } from '~/routes/gameday';
import { Route as GamedayEventRoute } from '~/routes/gameday.$eventCode';

describe('gameday route', () => {
  test('titles the page GameDay', () => {
    expect(runHead(GamedayRoute)?.meta?.[0]).toEqual({
      title: 'GameDay - The Blue Alliance',
    });
  });

  test('coerces the layout search param to a number', () => {
    expect(runValidateSearch(GamedayRoute, { layout: '3' })).toEqual({
      layout: 3,
    });
  });
});

describe('gameday event route', () => {
  test('redirects to gameday with the event preselected', () => {
    expect(() =>
      GamedayEventRoute.options.beforeLoad?.({
        params: { eventCode: '2024casj' },
      } as never),
    ).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/gameday',
          search: { event: '2024casj' },
        }),
      }),
    );
  });
});
