import { TZDate } from '@date-fns/tz';
import { addDays, parseISO, startOfWeek } from 'date-fns';

import { Event } from '~/api/tba/read/types.gen';
import { EventType } from '~/lib/api/EventType';

/**
 * Parse a YYYY-MM-DD date string as midnight in the event's timezone.
 * Falls back to user-local time (parseISO) if no timezone is provided.
 *
 * Uses the TZDate integer constructor (year, month, day, tz) rather than
 * the string form because the string form is affected by vitest fake timers.
 */
export function parseEventDate(
  dateStr: string,
  timezone: string | null | undefined,
): Date {
  if (timezone) {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new TZDate(year, month - 1, day, timezone);
  }
  return parseISO(dateStr);
}

export function isValidEventKey(key: string) {
  return /^[1-9]\d{3}(\d{2})?[a-z]+[0-9]{0,3}$/.test(key);
}

export function sortEventsComparator(a: Event, b: Event) {
  // First sort by date
  const start_date_a = parseISO(a.start_date);
  const start_date_b = parseISO(b.start_date);
  const end_date_a = parseISO(a.end_date);
  const end_date_b = parseISO(b.end_date);
  if (start_date_a < start_date_b) {
    return -1;
  }
  if (start_date_a > start_date_b) {
    return 1;
  }
  if (end_date_a < end_date_b) {
    return -1;
  }
  if (end_date_a > end_date_b) {
    return 1;
  }

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
  // parseISO treats YYYY-MM-DD as local midnight, matching toLocaleDateString behavior.
  const startDate = parseISO(event.start_date);
  const endDate = parseISO(event.end_date);

  const endDateString = endDate.toLocaleDateString('default', {
    month: month,
    day: 'numeric',
    year: 'numeric',
  });

  if (startDate.getTime() === endDate.getTime()) {
    return endDateString;
  }

  const startDateString = startDate.toLocaleDateString('default', {
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
  const now = new Date();
  // startOfWeek gives midnight on Monday in local time, not "current time on Monday".
  // This is consistent with parseISO which also gives local midnight for date strings.
  const weekStart = startOfWeek(now, { weekStartsOn: 1 });
  const weekEnd = addDays(weekStart, 7);

  const filteredEvents = events.filter((event) => {
    const startDate = parseISO(event.start_date);
    const endDate = parseISO(event.end_date);
    // Include events that overlap with [weekStart, weekEnd):
    // started before the end of this week AND ends on or after Monday.
    return startDate < weekEnd && endDate >= weekStart;
  });

  return sortEvents(filteredEvents);
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
  // Dates are interpreted in the event's timezone so that, e.g., an event
  // ending April 12 in New York ends at New York midnight, not the user's midnight.
  const startDate = parseEventDate(event.start_date, event.timezone);
  const endDate = parseEventDate(event.end_date, event.timezone);
  const now = new Date();
  const windowStart = addDays(startDate, -negativeDaysBefore);
  // endDate is midnight at the start of the last day, so +1 day to include
  // the full last day, then positiveDaysAfter additional days beyond that.
  const windowEnd = addDays(endDate, 1 + positiveDaysAfter);
  return now >= windowStart && now <= windowEnd;
}

export function isEventWithinADay(event: Event): boolean {
  return isEventWithinDays(event, -1, 1);
}
