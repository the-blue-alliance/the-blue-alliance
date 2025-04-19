import { type ClassValue, clsx } from 'clsx';
import React from 'react';
import { Params } from 'react-router';
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
  timezone: string | null,
): boolean {
  const date1 = new Date(timestamp1 * 1000);
  const date2 = new Date(timestamp2 * 1000);

  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: timezone ?? 'UTC',
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

export const USA_STATE_ABBREVIATION_TO_FULL = new Map<string, string>([
  ['AL', 'Alabama'],
  ['AK', 'Alaska'],
  ['AS', 'American Samoa'],
  ['AZ', 'Arizona'],
  ['AR', 'Arkansas'],
  ['CA', 'California'],
  ['CO', 'Colorado'],
  ['CT', 'Connecticut'],
  ['DE', 'Delaware'],
  ['DC', 'District of Columbia'],
  ['FL', 'Florida'],
  ['GA', 'Georgia'],
  ['GU', 'Guam'],
  ['HI', 'Hawaii'],
  ['ID', 'Idaho'],
  ['IL', 'Illinois'],
  ['IN', 'Indiana'],
  ['IA', 'Iowa'],
  ['KS', 'Kansas'],
  ['KY', 'Kentucky'],
  ['LA', 'Louisiana'],
  ['ME', 'Maine'],
  ['MD', 'Maryland'],
  ['MA', 'Massachusetts'],
  ['MI', 'Michigan'],
  ['MN', 'Minnesota'],
  ['MS', 'Mississippi'],
  ['MO', 'Missouri'],
  ['MT', 'Montana'],
  ['NE', 'Nebraska'],
  ['NV', 'Nevada'],
  ['NH', 'New Hampshire'],
  ['NJ', 'New Jersey'],
  ['NM', 'New Mexico'],
  ['NY', 'New York'],
  ['NC', 'North Carolina'],
  ['ND', 'North Dakota'],
  ['OH', 'Ohio'],
  ['OK', 'Oklahoma'],
  ['OR', 'Oregon'],
  ['PA', 'Pennsylvania'],
  ['PR', 'Puerto Rico'],
  ['RI', 'Rhode Island'],
  ['SC', 'South Carolina'],
  ['SD', 'South Dakota'],
  ['TN', 'Tennessee'],
  ['TX', 'Texas'],
  ['UT', 'Utah'],
  ['VT', 'Vermont'],
  ['VI', 'Virgin Islands'],
  ['VA', 'Virginia'],
  ['WA', 'Washington'],
  ['WV', 'West Virginia'],
  ['WI', 'Wisconsin'],
  ['WY', 'Wyoming'],
]);

export const STATE_TO_ABBREVIATION = new Map<string, string>(
  Array.from(USA_STATE_ABBREVIATION_TO_FULL.entries()).map(
    ([abbr, fullName]) => [fullName, abbr],
  ),
);

// https://stackoverflow.com/a/70806192
export function median(arr: number[]): number | undefined {
  if (!arr.length) {
    return undefined;
  }

  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

export function camelCaseToHumanReadable(camelCaseStr: string): string {
  // Insert a space before each uppercase letter and convert the result to lowercase
  const withSpaces = camelCaseStr.replace(/([A-Z])/g, ' $1');
  // Capitalize the first letter and return the result
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1);
}

export function splitIntoNChunks<T>(array: T[], numChunks: number): T[][] {
  if (array.length === 0) {
    return [];
  }

  const actualNumChunks = Math.min(numChunks, array.length);

  // Calculate the base size of each chunk
  const chunkSize = Math.floor(array.length / actualNumChunks);

  // Calculate how many chunks need an extra element
  const remainder = array.length % actualNumChunks;

  const result: T[][] = [];
  let currentIndex = 0;

  for (let i = 0; i < actualNumChunks; i++) {
    // Determine if this chunk needs an extra element
    const currentChunkSize = i < remainder ? chunkSize + 1 : chunkSize;

    result.push(array.slice(currentIndex, currentIndex + currentChunkSize));
    currentIndex += currentChunkSize;
  }

  return result;
}

// Reduces boilerplate when using react-query and API functions.
// Makes it so you don't have to call <response>.data.data, just <response>.data.
export async function queryFromAPI<T>(
  apiPromise: Promise<
    | {
        status: 200;
        data: T;
      }
    | {
        status: 304;
      }
    | {
        status: 401;
        data: {
          Error: string;
        };
      }
    | {
        status: 404;
      }
  >,
): Promise<T> {
  const resp = await apiPromise;
  if (resp.status === 200) {
    return Promise.resolve(resp.data);
  }

  return Promise.reject(new Error(resp.status.toString()));
}
