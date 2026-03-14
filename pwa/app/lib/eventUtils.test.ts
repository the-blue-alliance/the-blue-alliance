import { Temporal } from 'temporal-polyfill';
import { describe, expect, test, vi } from 'vitest';

import { Event } from '~/api/tba/read';
import {
  getCurrentWeekEvents,
  getEventDateString,
  getEventWeekString,
  isEventActive,
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
  test('includes current date within event range', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
    };
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-04-11T12:00:00Z'));
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
    vi.setSystemTime(new Date('2024-04-09T12:00:00Z'));
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
    vi.setSystemTime(new Date('2024-04-13T12:00:00Z'));
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
    vi.setSystemTime(new Date('2024-04-12T18:00:00Z'));
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
    vi.setSystemTime(new Date('2024-04-15T12:00:00Z'));
    expect(isEventWithinDays(event, 1, 1)).toBe(false);
    vi.useRealTimers();
  });
});

describe('getCurrentWeekEvents', () => {
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

  // Timezone bug: new Date('2024-04-08') parses as UTC midnight, but
  // closestStartMonday is at the user's current local time on Monday (e.g., noon).
  // A Monday event would have timeOffsetDays = -1 and be excluded.
  test('includes event that starts on Monday of the current week', () => {
    vi.useFakeTimers();
    // Thursday April 11, noon UTC — closestStartMonday would be April 8 at noon UTC
    vi.setSystemTime(new Date('2024-04-11T12:00:00Z'));

    const mondayEvent = {
      start_date: '2024-04-08',
      end_date: '2024-04-08',
    } as Event;

    const result = getCurrentWeekEvents([mondayEvent]);
    expect(result).toContain(mondayEvent);
    vi.useRealTimers();
  });

  // Timezone bug: for a user in UTC-5, the system time on Thursday morning UTC
  // might still be Wednesday in local time — verify PlainDate (not raw timestamp)
  // is used so we get Thursday's week, not Wednesday's.
  test('uses user local date to determine current week (UTC-5 simulation)', () => {
    vi.useFakeTimers();
    // Simulate user whose local date is Thursday April 11 (e.g., UTC-5 at noon)
    vi.spyOn(Temporal.Now, 'plainDateISO').mockReturnValue(
      Temporal.PlainDate.from('2024-04-11'),
    );

    const mondayEvent = {
      start_date: '2024-04-08',
      end_date: '2024-04-08',
    } as Event;
    const sundayPreviousWeek = {
      start_date: '2024-04-07',
      end_date: '2024-04-07',
    } as Event;

    const result = getCurrentWeekEvents([mondayEvent, sundayPreviousWeek]);
    expect(result).toContain(mondayEvent);
    expect(result).not.toContain(sundayPreviousWeek);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });
});

describe('isEventWithinDays timezone handling', () => {
  // Bug: getLocalMidnightOnDate uses the USER's timezone (UTC in test env),
  // but event dates should be interpreted in the EVENT's timezone.
  // An Eastern event (UTC-4) with start_date='2024-04-10' actually starts at
  // 2024-04-10T04:00:00Z. Before the fix, it incorrectly starts at 00:00 UTC.
  test('event in Eastern timezone (UTC-4): not in window before local midnight', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York', // UTC-4 in April
    };
    vi.useFakeTimers();
    // 02:00 UTC = 22:00 Eastern on April 9 — event has NOT started in its own timezone
    vi.setSystemTime(new Date('2024-04-10T02:00:00Z'));
    expect(isEventWithinDays(event, 0, 0)).toBe(false);
    vi.useRealTimers();
  });

  test('event in Eastern timezone (UTC-4): in window after local midnight', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York', // UTC-4 in April
    };
    vi.useFakeTimers();
    // 06:00 UTC = 02:00 Eastern on April 10 — event HAS started in its own timezone
    vi.setSystemTime(new Date('2024-04-10T06:00:00Z'));
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('event in Eastern timezone (UTC-4): still in window near end of last day', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York', // UTC-4 in April
    };
    vi.useFakeTimers();
    // 2024-04-13T02:00:00Z = April 12 22:00 Eastern — still April 12 in event tz
    vi.setSystemTime(new Date('2024-04-13T02:00:00Z'));
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });

  test('event in Eastern timezone (UTC-4): not in window after local midnight on day after end', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-12',
      timezone: 'America/New_York', // UTC-4 in April
    };
    vi.useFakeTimers();
    // 2024-04-13T05:00:00Z = April 13 01:00 Eastern — April 13, past the event end
    vi.setSystemTime(new Date('2024-04-13T05:00:00Z'));
    expect(isEventWithinDays(event, 0, 0)).toBe(false);
    vi.useRealTimers();
  });

  test('event in Western timezone (UTC+12): in window well before UTC midnight', () => {
    // @ts-expect-error: Don't need to fill out all the fields
    const event: Event = {
      start_date: '2024-04-10',
      end_date: '2024-04-10',
      timezone: 'Pacific/Auckland', // UTC+12 in April
    };
    vi.useFakeTimers();
    // April 9 13:00 UTC = April 10 01:00 Auckland — event HAS started locally
    vi.setSystemTime(new Date('2024-04-09T13:00:00Z'));
    expect(isEventWithinDays(event, 0, 0)).toBe(true);
    vi.useRealTimers();
  });
});

describe('getCurrentWeekEvents 8am-6pm window', () => {
  // PlainDate comparison missed this: an Auckland event with start_date='2024-04-15'
  // (Monday in Auckland) starts at April 15 8am NZST = April 14 8pm UTC = April 14 4pm
  // Eastern, which IS within the user's Monday April 8 – Sunday April 14 Eastern week.
  test('includes Auckland event whose active window falls on user Sunday', () => {
    vi.useFakeTimers();
    // Thursday April 11, noon Eastern. Week = April 8–14 Eastern.
    vi.setSystemTime(new Date('2024-04-11T16:00:00Z')); // noon Eastern
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('America/New_York');

    const aucklandEvent = {
      start_date: '2024-04-15', // Monday in Auckland = Sunday evening UTC
      end_date: '2024-04-15',
      timezone: 'Pacific/Auckland',
    } as Event;

    const result = getCurrentWeekEvents([aucklandEvent]);
    expect(result).toContain(aucklandEvent);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  // An event whose 6pm end is before Monday 00:00 in the user's tz should be excluded.
  test('excludes Sunday event whose 6pm end is before user Monday midnight', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-04-11T16:00:00Z'));
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('America/New_York');

    // Sunday April 7 in Eastern: 6pm = April 7 22:00 UTC. Week starts April 8 04:00 UTC.
    const sundayEvent = {
      start_date: '2024-04-07',
      end_date: '2024-04-07',
      timezone: 'America/New_York',
    } as Event;

    expect(getCurrentWeekEvents([sundayEvent])).not.toContain(sundayEvent);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  // Events without a timezone should use the Eastern fallback.
  test('uses Eastern fallback timezone when event has no timezone', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-04-11T16:00:00Z'));
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('America/New_York');

    // An event with no timezone, starting on Tuesday April 9 — should be included.
    const noTzEvent = {
      start_date: '2024-04-09',
      end_date: '2024-04-09',
      // timezone intentionally omitted (undefined → fallback to Eastern)
    } as Event;

    expect(getCurrentWeekEvents([noTzEvent])).toContain(noTzEvent);
    vi.restoreAllMocks();
    vi.useRealTimers();
  });
});

describe('isEventActive', () => {
  function makeEvent(
    start_date: string,
    end_date: string,
    timezone: string | null = 'America/New_York',
  ): Event {
    // @ts-expect-error: Don't need to fill out all the fields
    return { start_date, end_date, timezone };
  }

  // Active = any moment between midnight start_date and midnight after end_date
  // in the event's timezone, so the button stays on even for early/late sessions.

  test('returns true during midday on an event day', () => {
    vi.useFakeTimers();
    // April 11 10:00 Eastern = April 11 14:00 UTC
    vi.setSystemTime(new Date('2024-04-11T14:00:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12'))).toBe(true);
    vi.useRealTimers();
  });

  test('returns true in the early hours of the first event day', () => {
    vi.useFakeTimers();
    // April 10 01:00 Eastern = April 10 05:00 UTC
    vi.setSystemTime(new Date('2024-04-10T05:00:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12'))).toBe(true);
    vi.useRealTimers();
  });

  test('returns true late on the last event day', () => {
    vi.useFakeTimers();
    // April 12 23:00 Eastern = April 13 03:00 UTC
    vi.setSystemTime(new Date('2024-04-13T03:00:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12'))).toBe(true);
    vi.useRealTimers();
  });

  test('returns false the day before start_date', () => {
    vi.useFakeTimers();
    // April 9 23:55 Eastern = April 10 03:55 UTC — still April 9 in Eastern
    vi.setSystemTime(new Date('2024-04-10T03:55:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12'))).toBe(false);
    vi.useRealTimers();
  });

  test('returns false after midnight on day after end_date', () => {
    vi.useFakeTimers();
    // April 13 01:00 Eastern = April 13 05:00 UTC — April 13 in Eastern
    vi.setSystemTime(new Date('2024-04-13T05:00:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12'))).toBe(false);
    vi.useRealTimers();
  });

  test('respects event timezone — Auckland event active just after local midnight', () => {
    vi.useFakeTimers();
    // April 10 01:00 NZST (Auckland UTC+12) = April 9 13:00 UTC
    vi.setSystemTime(new Date('2024-04-09T13:00:00Z'));
    expect(
      isEventActive(makeEvent('2024-04-10', '2024-04-10', 'Pacific/Auckland')),
    ).toBe(true);
    vi.useRealTimers();
  });

  test('uses Eastern fallback when event timezone is null', () => {
    vi.useFakeTimers();
    // April 11 10:00 Eastern = April 11 14:00 UTC
    vi.setSystemTime(new Date('2024-04-11T14:00:00Z'));
    expect(isEventActive(makeEvent('2024-04-10', '2024-04-12', null))).toBe(
      true,
    );
    vi.useRealTimers();
  });
});
