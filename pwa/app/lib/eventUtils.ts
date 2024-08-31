import { Event } from '~/api/v3';

import { convertMsToDays, parseDate } from './utils';

export function sortEventsComparator(a: Event, b: Event) {
  // First sort by date
  const start_date_a = new Date(a.start_date);
  const start_date_b = new Date(b.start_date);
  const end_date_a = new Date(a.end_date);
  const end_date_b = new Date(b.end_date);
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
  // Then sort by name
  if (a.name < b.name) {
    return -1;
  }
  if (a.name > b.name) {
    return 1;
  }
  return 0;
}

/** Returns a Date object at midnight in the user's timezone on the specified YYYY-MM-DD. */
function getLocalMidnightOnDate(yyyymmdd: string) {
  const date = new Date(yyyymmdd + 'T00:00:00Z');
  return new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

export function getEventDateString(event: Event, month: 'long' | 'short') {
  // Local dates are needed since the toLocaleDateString depends on the user's local timezone.
  const startDate = getLocalMidnightOnDate(event.start_date);
  const endDate = getLocalMidnightOnDate(event.end_date);

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
  //const now = new Date('Jul 17, 2024');
  const filteredEvents = [];

  const diffFromWeekStart = now.getDay();
  const closestStartMonday = new Date(now).setDate(
    now.getDate() - diffFromWeekStart,
  );

  for (const event of events) {
    const startDate = parseDate(event.start_date);

    const timeOffsetDays = Math.floor(
      convertMsToDays(startDate - closestStartMonday),
    );

    if (timeOffsetDays === 0 || (timeOffsetDays > 0 && timeOffsetDays < 7)) {
      filteredEvents.push(event);
    }
  }
  return filteredEvents;
}

export function sortEvents(events: Event[]) {
  return events.sort((a, b) => sortEventsComparator(a, b));
}
