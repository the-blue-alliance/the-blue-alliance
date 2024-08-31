import { Params } from '@remix-run/react';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { getStatus } from '~/api/v3';

// TODO: Generate this from the API
const VALID_YEARS: number[] = [];
for (let i = 2024; i >= 1992; i--) {
  VALID_YEARS.push(i);
}
export { VALID_YEARS };

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function removeNonNumeric(str: string): string {
  return str.replace(/\D/g, '');
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
}

export async function parseParamsForYearElseDefault(
  params: Params,
): Promise<number | undefined> {
  if (params.year === undefined) {
    // TODO: Cache this call
    const status = await getStatus({});
    return status.status === 200
      ? status.data.current_season
      : new Date().getFullYear();
  }

  const year = Number(params.year);
  if (Number.isNaN(year) || year <= 0) {
    return undefined;
  }

  return year;
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

export function parseDate(date: string) {
  const [year, month, day] = date.split('-').map(Number);
  return new Date(year, month - 1, day).getTime();
}

export function convertMsToDays(time: number) {
  return time / (1000 * 60 * 60 * 24);
}
