import { afterEach, describe, expect, test, vi } from 'vitest';

import { Event } from '~/api/tba/read';
import {
  getCurrentWeekEvents,
  getEventDateString,
  getEventWeekString,
  isEventWithinDays,
  isValidEventKey,
} from '~/lib/eventUtils';

describe.concurrent('isValidEventKey', () => {
  test.each(['2010ct', '2014onto2', '202121fim', '2022dc305'])(
    'valid event key',
    (key) => {
      expect(isValidEventKey(key)).toBe(true);
    },
  );

  test.each(['210c1', 'frc2010ct', '2010 ct'])('invalid event key', (key) => {
    expect(isValidEventKey(key)).toBe(false);
  });
});

describe.concurrent('getEventDateString', () => {
  test('Same start and end date', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-01-01',
      end_date: '2024-01-01',
    };
    expect(getEventDateString(event, 'short')).toEqual('Jan 1, 2024');
  });

  test('Different start and end dates', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-01-01',
      end_date: '2024-01-03',
    };
    expect(getEventDateString(event, 'short')).toEqual('Jan 1 to Jan 3, 2024');
  });

  test('Different month start and end dates', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-03-30',
      end_date: '2024-04-01',
    };
    expect(getEventDateString(event, 'short')).toEqual('Mar 30 to Apr 1, 2024');
  });
});

describe.concurrent('getEventWeekString', () => {
  test('Null year', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2024,
      week: null,
    };
    expect(getEventWeekString(event)).toEqual(null);
  });

  test('Nominal case', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2024,
      week: 0,
    };
    expect(getEventWeekString(event)).toEqual('Week 1');
  });

  test('2016 special case', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event1: Event = {
      year: 2016,
      week: 0,
    };
    expect(getEventWeekString(event1)).toEqual('Week 0.5');

    // @ts-expect-error: Don't need to fill out all the fields
    const event2: Event = {
      year: 2016,
      week: 1,
    };
    expect(getEventWeekString(event2)).toEqual('Week 1');
  });

  test('2021 special case: Participation', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2021,
      week: 0,
    };
    expect(getEventWeekString(event)).toEqual('Participation');
  });

  test('2021 special case: Innovation', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2021,
      week: 6,
    };
    expect(getEventWeekString(event)).toEqual('FIRST Innovation Challenge');
  });

  test('2021 special case: IR@H', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2021,
      week: 7,
    };
    expect(getEventWeekString(event)).toEqual(
      'INFINITE RECHARGE At Home Challenge',
    );
  });

  test('2021 special case: GDC', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2021,
      week: 8,
    };
    expect(getEventWeekString(event)).toEqual('Game Design Challenge');
  });

  test('2021 special case: Awards', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      year: 2021,
      week: 9,
    };
    expect(getEventWeekString(event)).toEqual('Awards');
  });
});

describe('isEventWithinDays', () => {
  // All setSystemTime calls use the local Date constructor (not UTC strings) so
  // the calendar date is the same in every timezone, matching parseISO behavior.

  test('uses event timezone: event in New York is still active at 11pm EDT on its end date', () => {
    // An event ending April 12 in New York ends at midnight April 13 EDT (04:00 UTC).
    // At 03:00 UTC on April 13 it is still April 12 in New York, so the event
    // should still be within the window.
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-04-13T03:00:00Z')); // 11pm EDT April 12
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('includes current date within event range', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0)); // April 11 noon local
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('allows checking days before start date', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 9, 12, 0, 0)); // April 9 noon local
    expect(isEventWithinDays(event, 1, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('includes days after end date', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 13, 12, 0, 0)); // April 13 noon local
    expect(isEventWithinDays(event, 0, 1)).toBe(true);
    vi.useRealTimers();
  });

  test('includes the full last day of the event with zero days after', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 12, 18, 0, 0)); // April 12 6pm local
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('returns false when outside configured window', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 15, 12, 0, 0)); // April 15 noon local
    expect(isEventWithinDays(event, 1, 1)).toBe(false);
    vi.useRealTimers();
  });
});

describe('getCurrentWeekEvents', () => {
  test('includes Monday event when today is Thursday at noon', () => {
    // Bug: closestStartMonday was computed at current time-of-day (noon),
    // not midnight. Monday events (midnight) < Monday noon, giving
    // timeOffsetDays=-1, then end < closestStartMonday → wrongly excluded.
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0)); // Thursday April 11, noon

    const mondayEvent = {
      start_date: '2024-04-08',
      end_date: '2024-04-08',
    } as Event;

    const result = getCurrentWeekEvents([mondayEvent]);
    expect(result).toContain(mondayEvent);
    vi.useRealTimers();
  });

  test('excludes previous Sunday but includes same-week events', () => {
    // Set to Thursday April 11 at noon local time
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0));

    // Sunday April 7 — before Monday week start
    const sundayBeforeEvent = {
      start_date: '2024-04-07',
      end_date: '2024-04-07',
    } as Event;
    // Thursday April 11 — clearly within the week
    const thursdayEvent = {
      start_date: '2024-04-11',
      end_date: '2024-04-11',
    } as Event;
    // Next Wednesday April 17 — clearly after the Mon-Sun week
    const nextWeekEvent = {
      start_date: '2024-04-17',
      end_date: '2024-04-17',
    } as Event;

    const result = getCurrentWeekEvents([
      sundayBeforeEvent,
      thursdayEvent,
      nextWeekEvent,
    ]);

    expect(result).toContain(thursdayEvent);
    expect(result).not.toContain(sundayBeforeEvent);
    expect(result).not.toContain(nextWeekEvent);
    vi.useRealTimers();
  });

  test('includes ongoing events that started before the current week', () => {
    // Set to Wednesday April 10 at noon local time
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 10, 12, 0, 0));

    // Started last week (April 3), ends this week (April 13) — still ongoing
    const ongoingEvent = {
      start_date: '2024-04-03',
      end_date: '2024-04-13',
    } as Event;
    // Started and ended last week — fully over
    const pastEvent = {
      start_date: '2024-04-03',
      end_date: '2024-04-06',
    } as Event;

    const result = getCurrentWeekEvents([ongoingEvent, pastEvent]);

    expect(result).toContain(ongoingEvent);
    expect(result).not.toContain(pastEvent);
    vi.useRealTimers();
  });
});

// These tests stub process.env.TZ to simulate different user locales.
// getCurrentWeekEvents uses parseISO (user-local time) for event dates and
// startOfWeek (user-local time) for week boundaries, so it is sensitive to
// the user's timezone.
describe('getCurrentWeekEvents user timezone sensitivity', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.useRealTimers();
  });

  test('Tokyo user (UTC+9) on Thursday noon still sees Monday event', () => {
    vi.stubEnv('TZ', 'Asia/Tokyo');
    vi.useFakeTimers();
    // Thursday April 11, noon Tokyo time
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0));

    const mondayEvent = {
      start_date: '2024-04-08',
      end_date: '2024-04-08',
    } as Event;

    expect(getCurrentWeekEvents([mondayEvent])).toContain(mondayEvent);
  });

  test('LA user (UTC-7) on Thursday noon sees Sunday event in the same week', () => {
    vi.stubEnv('TZ', 'America/Los_Angeles');
    vi.useFakeTimers();
    // Thursday April 11, noon LA time
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0));

    const sundayEvent = {
      start_date: '2024-04-14',
      end_date: '2024-04-14',
    } as Event;

    expect(getCurrentWeekEvents([sundayEvent])).toContain(sundayEvent);
  });

  test('LA user does not see next-Monday event as this week', () => {
    vi.stubEnv('TZ', 'America/Los_Angeles');
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2024, 3, 11, 12, 0, 0)); // Thursday April 11

    const nextMondayEvent = {
      start_date: '2024-04-15',
      end_date: '2024-04-15',
    } as Event;

    expect(getCurrentWeekEvents([nextMondayEvent])).not.toContain(
      nextMondayEvent,
    );
  });
});

// isEventWithinDays uses event.timezone for date boundaries, so the result
// should be the same regardless of the user's local timezone.
describe('isEventWithinDays user timezone independence', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.useRealTimers();
  });

  test('Tokyo user and LA user see the same active/inactive result for a New York event', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York',
    };

    vi.useFakeTimers();
    // 03:00 UTC = 23:00 EDT April 12 → event still active in New York
    vi.setSystemTime(new Date('2024-04-13T03:00:00Z'));

    vi.stubEnv('TZ', 'Asia/Tokyo'); // 12:00 noon April 13 in Tokyo
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.unstubAllEnvs();

    vi.stubEnv('TZ', 'America/Los_Angeles'); // 8pm April 12 in LA
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.unstubAllEnvs();

    // 05:00 UTC = 01:00 EDT April 13 → event ended in New York
    vi.setSystemTime(new Date('2024-04-13T05:00:00Z'));

    vi.stubEnv('TZ', 'Asia/Tokyo');
    expect(isEventWithinDays(event, 0, 0)).toBe(false);
    vi.unstubAllEnvs();

    vi.stubEnv('TZ', 'America/Los_Angeles');
    expect(isEventWithinDays(event, 0, 0)).toBe(false);
  });
});
