import { Params } from '@remix-run/react';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { getStatus } from '~/api/v3';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function removeNonNumeric(str: string): string {
  return str.replace(/\D/g, '');
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
