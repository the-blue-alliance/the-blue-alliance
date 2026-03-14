import { Temporal } from 'temporal-polyfill';

import { Event } from '~/api/tba/read/types.gen';
import { EventType } from '~/lib/api/EventType';

/** IANA timezone used when an event has no timezone field. */
export const EVENT_FALLBACK_TIMEZONE = 'America/New_York';
/** Hour (0–23) when events start each day in the event's local timezone. */
export const EVENT_START_HOUR = 8;
/** Hour (0–23) when events end each day in the event's local timezone. */
export const EVENT_END_HOUR = 18;

const EVENT_START_TIME = Temporal.PlainTime.from({ hour: EVENT_START_HOUR });
const EVENT_END_TIME = Temporal.PlainTime.from({ hour: EVENT_END_HOUR });

// Defaults to EVENT_FALLBACK_TIMEZONE, but may want to introduce some semi-intelligent guessing in the future.
function getEventTz(event: Event): string {
  return event.timezone ?? EVENT_FALLBACK_TIMEZONE;
}

/** Returns the instants when the event opens (8am start_date) and closes (6pm end_date). */
function getEventActiveWindow(event: Event): {
  start: Temporal.Instant;
  end: Temporal.Instant;
} {
  const tz = getEventTz(event);
  return {
    start: Temporal.PlainDate.from(event.start_date)
      .toZonedDateTime({ timeZone: tz, plainTime: EVENT_START_TIME })
      .toInstant(),
    end: Temporal.PlainDate.from(event.end_date)
      .toZonedDateTime({ timeZone: tz, plainTime: EVENT_END_TIME })
      .toInstant(),
  };
}

export function isValidEventKey(key: string) {
  return /^[1-9]\d{3}(\d{2})?[a-z]+[0-9]{0,3}$/.test(key);
}

export function sortEventsComparator(a: Event, b: Event) {
  // First sort by date
  const startCompare = Temporal.PlainDate.compare(
    Temporal.PlainDate.from(a.start_date),
    Temporal.PlainDate.from(b.start_date),
  );
  if (startCompare !== 0) return startCompare;

  const endCompare = Temporal.PlainDate.compare(
    Temporal.PlainDate.from(a.end_date),
    Temporal.PlainDate.from(b.end_date),
  );
  if (endCompare !== 0) return endCompare;

  // If one of the events is DCMP finals or CMP finals, put it last
  // e.g.: [2024necmp1, 2024necmp2, 2024necmp]
  if (
    (a.event_type === EventType.CMP_FINALS ||
      a.event_type === EventType.DISTRICT_CMP ||
      b.event_type === EventType.CMP_FINALS ||
      b.event_type === EventType.DISTRICT_CMP) &&
    a.event_type !== b.event_type
  ) {
    return a.event_type === EventType.CMP_FINALS ||
      a.event_type === EventType.DISTRICT_CMP
      ? 1
      : -1;
  }

  // Then sort by name
  if (a.name < b.name) {
    return -1;
  }
  if (a.name > b.name) {
    return 1;
  }
  return 0;
}

export function getEventDateString(event: Event, month: 'long' | 'short') {
  // PlainDate has no time or timezone component, so formatting is locale-only.
  const startDate = Temporal.PlainDate.from(event.start_date);
  const endDate = Temporal.PlainDate.from(event.end_date);

  const endDateString = endDate.toLocaleString('default', {
    month: month,
    day: 'numeric',
    year: 'numeric',
  });

  if (Temporal.PlainDate.compare(startDate, endDate) === 0) {
    return endDateString;
  }

  const startDateString = startDate.toLocaleString('default', {
    month: month,
    day: 'numeric',
  });

  return `${startDateString} to ${endDateString}`;
}

export function getEventWeekString(event: Event) {
  if (event.week === null) {
    return null;
  }
  switch (event.year) {
    case 2016:
      return event.week === 0 ? 'Week 0.5' : `Week ${event.week}`;
    case 2021: {
      switch (event.week) {
        case 0:
          return 'Participation';
        case 6:
          return 'FIRST Innovation Challenge';
        case 7:
          return 'INFINITE RECHARGE At Home Challenge';
        case 8:
          return 'Game Design Challenge';
        case 9:
          return 'Awards';
        default:
          return null;
      }
    }
    default:
      return `Week ${event.week + 1}`;
  }
}

export function getCurrentWeekEvents(events: Event[]) {
  // Build the user's week window as Instants so we can compare against the
  // event's active window (8am–6pm in the event's timezone) correctly even
  // when the two timezones are far apart.
  const userTz = Temporal.Now.timeZoneId();
  const today = Temporal.Now.plainDateISO(userTz);
  // ISO day-of-week: 1 = Monday … 7 = Sunday
  const monday = today.subtract({ days: today.dayOfWeek - 1 });
  const weekStart = monday.toZonedDateTime(userTz).toInstant();
  // Exclusive upper bound: next Monday at 00:00 in the user's timezone.
  const weekEnd = monday.add({ days: 7 }).toZonedDateTime(userTz).toInstant();

  const filteredEvents = [];
  for (const event of events) {
    const { start: eventStart, end: eventEnd } = getEventActiveWindow(event);
    // Include if the event's active window overlaps with the user's week at all.
    if (
      Temporal.Instant.compare(eventStart, weekEnd) < 0 &&
      Temporal.Instant.compare(eventEnd, weekStart) > 0
    ) {
      filteredEvents.push(event);
    }
  }
  return sortEvents(filteredEvents);
}

/**
 * Returns true on any calendar day the event is scheduled, from midnight on
 * start_date through midnight at the end of end_date (event's timezone).
 * The window is intentionally wide so the Watch Now button is active even if
 * the event runs early or late.
 */
export function isEventActive(event: Event): boolean {
  if (!event.start_date || !event.end_date) return false;
  return isEventWithinDays(event, 0, 0);
}

export function sortEvents(events: Event[]) {
  return events.sort((a, b) => sortEventsComparator(a, b));
}

// Common division names and their shortforms for Einstein events
export const DIVISION_SHORTFORMS: Record<string, string> = {
  Newton: 'New',
  Einstein: 'Ein',
  Curie: 'Cur',
  Galileo: 'Gal',
  Hopper: 'Hop',
  Tesla: 'Tes',
  Turing: 'Tur',
  Archimedes: 'Arc',
  Carson: 'Car',
  Carver: 'Crv',
  Daly: 'Dal',
  Darwin: 'Dar',
  Johnson: 'Joh',
  Milstein: 'Mil',
  Roebling: 'Roe',
};

// Helper to get division shortform (e.g., "Newton Division" -> "New")
export function getDivisionShortform(divisionName: string): string {
  // Try to match the division name
  for (const [fullName, shortForm] of Object.entries(DIVISION_SHORTFORMS)) {
    if (divisionName.includes(fullName)) {
      return shortForm;
    }
  }

  // If no match found, take first 3 letters
  return divisionName.substring(0, 3);
}

export function isEventWithinDays(
  event: Event,
  negativeDaysBefore: number,
  positiveDaysAfter: number,
): boolean {
  if (event.start_date === null || event.end_date === null) {
    return false;
  }
  // Use the event's own timezone so that "midnight" refers to the event's
  // local midnight, not the user's. Falls back to EVENT_FALLBACK_TIMEZONE.
  const eventTimeZone = getEventTz(event);
  const startDate = Temporal.PlainDate.from(event.start_date);
  const endDate = Temporal.PlainDate.from(event.end_date);

  // Window opens negativeDaysBefore days before midnight of start_date in the
  // event's timezone.
  const windowStart = startDate
    .subtract({ days: negativeDaysBefore })
    .toZonedDateTime(eventTimeZone)
    .toInstant();

  // endDate is the last calendar day. +1 moves to the next midnight (end of
  // the last day), then positiveDaysAfter extends further.
  const windowEnd = endDate
    .add({ days: 1 + positiveDaysAfter })
    .toZonedDateTime(eventTimeZone)
    .toInstant();

  const now = Temporal.Now.instant();
  return (
    Temporal.Instant.compare(now, windowStart) >= 0 &&
    Temporal.Instant.compare(now, windowEnd) <= 0
  );
}

export function isEventWithinADay(event: Event): boolean {
  return isEventWithinDays(event, -1, 1);
}
