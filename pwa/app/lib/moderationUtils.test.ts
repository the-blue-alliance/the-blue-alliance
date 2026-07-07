import { Temporal } from 'temporal-polyfill';
import { describe, expect, test } from 'vitest';

import {
  SUGGESTION_TYPE_ORDER,
  defaultExpirationDays,
  defaultSetPreferred,
  formatAuthorReputation,
  formatEventDateRange,
  groupSuggestionsByTargetKey,
  matchVideoDurationWarning,
  matchVideoTitleWarning,
  socialProfileWarning,
  suggestionTypeOrderComparator,
  summarizeReviewOutcomes,
} from '~/lib/moderationUtils';

describe.concurrent('groupSuggestionsByTargetKey', () => {
  test('groups by target key preserving first-seen order', () => {
    const suggestions = [
      { key: 'a', target_key: '2026np' },
      { key: 'b', target_key: '2026mods' },
      { key: 'c', target_key: '2026np' },
    ];
    expect(groupSuggestionsByTargetKey(suggestions)).toEqual([
      {
        targetKey: '2026np',
        suggestions: [
          { key: 'a', target_key: '2026np' },
          { key: 'c', target_key: '2026np' },
        ],
      },
      {
        targetKey: '2026mods',
        suggestions: [{ key: 'b', target_key: '2026mods' }],
      },
    ]);
  });
});

describe.concurrent('socialProfileWarning', () => {
  test('accepts plain profile identifiers', () => {
    expect(
      socialProfileWarning('facebook-profile', 'thebluealliance'),
    ).toBeUndefined();
    expect(
      socialProfileWarning('instagram-profile', 'the_blue_alliance'),
    ).toBeUndefined();
    expect(
      socialProfileWarning('twitter-profile', 'thebluealliance'),
    ).toBeUndefined();
    expect(
      socialProfileWarning('github-profile', 'the-blue-alliance'),
    ).toBeUndefined();
  });

  test('accepts valid youtube channel forms', () => {
    for (const key of [
      '@FIRSTRoboticsCompetition',
      'channel/UCkWfzJTG5j4V8AhqDRCE5Cw',
      'c/TheBlueAlliance',
      'user/FRCTeamsGlobal',
      'FRCTeamsGlobal',
    ]) {
      expect(socialProfileWarning('youtube-channel', key)).toBeUndefined();
    }
  });

  test('flags facebook personal profile and group links', () => {
    expect(
      socialProfileWarning('facebook-profile', 'profile.php?id=1000123'),
    ).toMatch(/personal profile/);
    expect(socialProfileWarning('facebook-profile', 'groups/frcteams')).toMatch(
      /group/,
    );
    expect(
      socialProfileWarning('facebook-profile', 'people/John-Doe/1000123'),
    ).toBeTruthy();
    expect(
      socialProfileWarning(
        'facebook-profile',
        'https://www.facebook.com/thebluealliance',
      ),
    ).toBeTruthy();
    expect(socialProfileWarning('facebook-profile', '100064531607957')).toMatch(
      /Numeric/,
    );
  });

  test('flags youtube video links posing as channels', () => {
    expect(
      socialProfileWarning('youtube-channel', 'watch?v=_fybREErgyM'),
    ).toMatch(/video/);
    expect(
      socialProfileWarning('youtube-channel', 'https://youtu.be/_fybREErgyM'),
    ).toMatch(/video/);
    expect(socialProfileWarning('youtube-channel', 'shorts/abc123')).toMatch(
      /video/,
    );
    expect(
      socialProfileWarning('youtube-channel', 'playlist?list=PL123'),
    ).toMatch(/video/);
  });

  test('flags malformed instagram and x handles', () => {
    expect(
      socialProfileWarning('instagram-profile', 'p/C4bhT7FsmAW'),
    ).toBeTruthy();
    expect(
      socialProfileWarning('twitter-profile', 'thebluealliance/status/123'),
    ).toBeTruthy();
  });

  test('unknown slugs and empty keys pass through', () => {
    expect(socialProfileWarning('imgur', 'whatever/thing')).toBeUndefined();
    expect(socialProfileWarning('facebook-profile', '')).toBeUndefined();
  });
});

describe.concurrent('defaultSetPreferred', () => {
  test('checked for images when the team has no preferred images', () => {
    expect(
      defaultSetPreferred({
        candidate_media: { is_image: true },
        existing_preferred: [],
      }),
    ).toBe(true);
  });

  test('unchecked when preferred images already exist', () => {
    expect(
      defaultSetPreferred({
        candidate_media: { is_image: true },
        existing_preferred: [{}],
      }),
    ).toBe(false);
  });

  test('unchecked for non-images', () => {
    expect(
      defaultSetPreferred({
        candidate_media: { is_image: false },
        existing_preferred: [],
      }),
    ).toBe(false);
  });
});

describe.concurrent('formatEventDateRange', () => {
  test('formats a short month-day range', () => {
    expect(formatEventDateRange('2016-03-24', '2016-03-27')).toBe(
      'Mar 24 – Mar 27',
    );
  });

  test('returns undefined when either date is missing', () => {
    expect(formatEventDateRange(null, '2016-03-27')).toBeUndefined();
    expect(formatEventDateRange('2016-03-24', undefined)).toBeUndefined();
  });
});

describe.concurrent('suggestionTypeOrderComparator', () => {
  test('sorts types into the web review home order', () => {
    const shuffled = [
      'api_auth_access',
      'offseason-event',
      'social-media',
      'match',
      'robot',
      'event',
      'event_media',
      'media',
    ];
    expect([...shuffled].sort(suggestionTypeOrderComparator)).toEqual(
      SUGGESTION_TYPE_ORDER,
    );
  });

  test('unknown types sort last', () => {
    expect(
      ['mystery-type', 'match'].sort(suggestionTypeOrderComparator),
    ).toEqual(['match', 'mystery-type']);
  });
});

describe.concurrent('defaultExpirationDays', () => {
  const today = Temporal.PlainDate.from('2026-07-03');

  test('event end + 7 days in the future defaults to 7', () => {
    expect(defaultExpirationDays('2026-07-10', today)).toBe(7);
  });

  test('event ending today defaults to 7', () => {
    expect(defaultExpirationDays('2026-07-03', today)).toBe(7);
  });

  test('event end + 7 days exactly today defaults to 7', () => {
    expect(defaultExpirationDays('2026-06-26', today)).toBe(7);
  });

  test('event end + 7 days in the past defaults to never', () => {
    expect(defaultExpirationDays('2026-06-25', today)).toBe(-1);
  });

  test('missing end date defaults to never', () => {
    expect(defaultExpirationDays(null, today)).toBe(-1);
    expect(defaultExpirationDays(undefined, today)).toBe(-1);
  });
});

describe.concurrent('summarizeReviewOutcomes', () => {
  test('joins outcome counts', () => {
    expect(
      summarizeReviewOutcomes({
        accepted: ['1', '2'],
        rejected: ['3'],
        alreadyReviewed: [],
      }),
    ).toBe('2 accepted · 1 rejected');
  });

  test('calls out suggestions someone else already reviewed', () => {
    expect(
      summarizeReviewOutcomes({
        accepted: [],
        rejected: [],
        alreadyReviewed: ['1'],
      }),
    ).toBe('1 already reviewed by someone else');
  });

  test('undefined when nothing was processed', () => {
    expect(
      summarizeReviewOutcomes({
        accepted: [],
        rejected: [],
        alreadyReviewed: [],
      }),
    ).toBeUndefined();
  });
});

describe.concurrent('formatAuthorReputation', () => {
  test('shows lifetime counts', () => {
    expect(
      formatAuthorReputation({ accepted_count: 234, rejected_count: 12 }),
    ).toBe('234 accepted · 12 rejected');
  });

  test('flags first-time suggesters', () => {
    expect(
      formatAuthorReputation({ accepted_count: 0, rejected_count: 0 }),
    ).toBe('first-time suggester');
  });

  test('undefined when counts are unavailable', () => {
    expect(formatAuthorReputation({})).toBeUndefined();
  });
});

describe.concurrent('matchVideoTitleWarning', () => {
  const event = { name: 'New England District Championship', year: 2016 };

  test('no warning when the title mentions the match key', () => {
    expect(
      matchVideoTitleWarning('2016 NE CMP F1M1', '2016necmp_f1m1', event),
    ).toBeUndefined();
  });

  test('no warning for spelled-out finals', () => {
    expect(
      matchVideoTitleWarning(
        'Final 1 - NE Championship',
        '2016necmp_f1m1',
        event,
      ),
    ).toBeUndefined();
  });

  test('no warning for qualification shorthand', () => {
    expect(
      matchVideoTitleWarning('Quals 57 - 2016 NECMP', '2016necmp_qm57', event),
    ).toBeUndefined();
  });

  test('no warning for double-elim playoff phrasing', () => {
    expect(
      matchVideoTitleWarning(
        'Playoff 5 - District Champs',
        '2023necmp_sf5m1',
        event,
      ),
    ).toBeUndefined();
  });

  test('warns when title mentions the event but not the match', () => {
    expect(
      matchVideoTitleWarning(
        '2016 New England Championship Saturday',
        '2016necmp_f1m1',
        event,
      ),
    ).toMatch(/doesn't mention F1M1/);
  });

  test('warns when title mentions neither match nor event', () => {
    expect(
      matchVideoTitleWarning('Cool robot montage', '2016necmp_f1m1', event),
    ).toMatch(/match or event/);
  });

  test('no warning without a title or parseable key', () => {
    expect(
      matchVideoTitleWarning(undefined, '2016necmp_f1m1', event),
    ).toBeUndefined();
    expect(matchVideoTitleWarning('title', '2016necmp', event)).toBeUndefined();
  });
});

describe.concurrent('matchVideoDurationWarning', () => {
  test('no warning for match-length videos', () => {
    expect(matchVideoDurationWarning(182, 'abc123')).toBeUndefined();
  });

  test('warns for long videos without a timestamp', () => {
    expect(matchVideoDurationWarning(8 * 3600, 'abc123')).toMatch(
      /480 minutes.*full-stream/,
    );
  });

  test('no warning for long videos with a timestamp', () => {
    expect(
      matchVideoDurationWarning(8 * 3600, 'abc123?t=4200'),
    ).toBeUndefined();
    expect(
      matchVideoDurationWarning(8 * 3600, 'abc123?start=4200'),
    ).toBeUndefined();
  });

  test('no warning when duration is unknown', () => {
    expect(matchVideoDurationWarning(undefined, 'abc123')).toBeUndefined();
    expect(matchVideoDurationWarning(null, 'abc123')).toBeUndefined();
  });
});
