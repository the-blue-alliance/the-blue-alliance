import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Award, Event, Match } from '~/api/v3';
import { AwardType, SORT_ORDER } from '~/lib/api/AwardType';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function parseDateString(date: string) {
  return new Date(date);
}

export function getEventDateString(event: Event, month: 'long' | 'short') {
  const startDate = parseDateString(event.start_date);
  const endDate = parseDateString(event.end_date);

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

export function removeNonNumeric(str: string): string {
  return str.replace(/\D/g, '');
}

export function sortMatchComparator(a: Match, b: Match) {
  const compLevelValues = {
    f: 5,
    sf: 4,
    qf: 3,
    ef: 2,
    qm: 1,
  };
  if (a.comp_level !== b.comp_level) {
    return compLevelValues[a.comp_level] - compLevelValues[b.comp_level];
  }

  return a.set_number - b.set_number || a.match_number - b.match_number;
}

export function sortAwardsComparator(a: Award, b: Award) {
  const orderA = SORT_ORDER[a.award_type as AwardType] ?? 1000;
  const orderB = SORT_ORDER[b.award_type as AwardType] ?? 1000;

  return orderA - orderB || a.award_type - b.award_type;
}

export function sortTeamKeysComparator(a: string, b: string) {
  return Number(removeNonNumeric(a)) - Number(removeNonNumeric(b));
}

export function sortEventsComparator(a: Event, b: Event) {
  // First sort by date
  const start_date_a = parseDateString(a.start_date);
  const start_date_b = parseDateString(b.start_date);
  const end_date_a = parseDateString(a.end_date);
  const end_date_b = parseDateString(b.end_date);
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

export function timestampsAreOnDifferentDays(
  timestamp1: number,
  timestamp2: number,
): boolean {
  const date1 = new Date(timestamp1 * 1000);
  const date2 = new Date(timestamp2 * 1000);

  return (
    date1.getFullYear() !== date2.getFullYear() ||
    date1.getMonth() !== date2.getMonth() ||
    date1.getDate() !== date2.getDate()
  );
}

export function zip<T extends unknown[]>(...arrays: (T | undefined)[]): T[] {
  if (arrays.length === 0) {
    return [];
  }

  // Treat undefined arrays as empty arrays
  const validArrays = arrays.map((arr) => arr ?? []);

  const minLength = Math.min(...validArrays.map((arr) => arr.length));

  const zipped: T[] = [];
  for (let i = 0; i < minLength; i++) {
    const tuple = validArrays.map((arr) => arr[i]) as T;
    zipped.push(tuple);
  }

  return zipped;
}
