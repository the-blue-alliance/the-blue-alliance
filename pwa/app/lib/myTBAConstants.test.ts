import { describe, expect, test } from 'vitest';

import {
  SUBSCRIPTION_TYPES,
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
} from '~/lib/myTBAConstants';

describe('SUBSCRIPTION_TYPES', () => {
  test('lists every notification type that has a display name', () => {
    expect(SUBSCRIPTION_TYPES).toEqual([
      'upcoming_match',
      'match_score',
      'alliance_selection',
      'awards_posted',
      'match_video_added',
    ]);
  });

  test('labels upcoming match notifications for the settings page', () => {
    expect(SUBSCRIPTION_TYPE_DISPLAY_NAMES.upcoming_match).toBe(
      'Upcoming Match',
    );
  });
});
