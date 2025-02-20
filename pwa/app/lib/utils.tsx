import { Params } from '@remix-run/react';
import { type ClassValue, clsx } from 'clsx';
import React from 'react';
import { twMerge } from 'tailwind-merge';

import { WltRecord, getStatus } from '~/api/v3';

// TODO: Generate this from the API
const VALID_YEARS: number[] = [];
for (let i = 2025; i >= 1992; i--) {
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
  timezone: string,
): boolean {
  const date1 = new Date(timestamp1 * 1000);
  const date2 = new Date(timestamp2 * 1000);

  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });

  const formattedDate1 = formatter.format(date1);
  const formattedDate2 = formatter.format(date2);

  return formattedDate1 !== formattedDate2;
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

export function convertMsToDays(time: number) {
  return time / (1000 * 60 * 60 * 24);
}

export function stringifyRecord(record: WltRecord): string {
  return `${record.wins}-${record.losses}-${record.ties}`;
}

export function pluralize(
  count: number,
  singular: string,
  plural: string,
  includeNumber = true,
) {
  return `${includeNumber ? `${count} ` : ''}${count === 1 ? singular : plural}`;
}

export function addRecords(record1: WltRecord, record2: WltRecord): WltRecord {
  return {
    wins: record1.wins + record2.wins,
    losses: record1.losses + record2.losses,
    ties: record1.ties + record2.ties,
  };
}

export function winrateFromRecord(record: WltRecord): number {
  return record.wins / Math.max(1, record.wins + record.losses + record.ties);
}

export function joinComponents(
  components: React.ReactNode[],
  joinString: string | React.ReactNode,
) {
  return components.map((comp, index) => (
    <React.Fragment key={index}>
      {comp}
      {index !== components.length - 1 && joinString}
    </React.Fragment>
  ));
}
