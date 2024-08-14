import { Event } from '~/api/v3';

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
