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

export function getEventDateString(event: Event, month: 'long' | 'short') {
  const startDate = new Date(event.start_date);
  const endDate = new Date(event.end_date);

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
  if (event.year == 2016) {
    return `Week ${event.week == 0 ? '0.5' : event.week}`;
  }
  if (event.year == 2021) {
    if (event.week == 0) {
      return 'Participation';
    }
    if (event.week == 6) {
      return 'FIRST Innovation Challenge';
    }
    if (event.week == 7) {
      return 'INFINITE RECHARGE At Home Challenge';
    }
    if (event.week == 8) {
      return 'Game Design Challenge';
    }
    return 'Awards';
  }
  return `Week ${event.week + 1}`;
}
