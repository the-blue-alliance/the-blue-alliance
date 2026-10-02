import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  copyCsvToClipboard,
  downloadCsv,
  escapeCsvField,
  generateCsv,
} from '~/lib/csvUtils';

describe('escapeCsvField', () => {
  test('plain text without special characters', () => {
    expect(escapeCsvField('hello')).toEqual('hello');
    expect(escapeCsvField('Team 254')).toEqual('Team 254');
    expect(escapeCsvField(123)).toEqual('123');
  });

  test('text with commas', () => {
    expect(escapeCsvField('San Jose, CA')).toEqual('"San Jose, CA"');
    expect(escapeCsvField('red, white, blue')).toEqual('"red, white, blue"');
  });

  test('text with quotes', () => {
    expect(escapeCsvField('He said "hello"')).toEqual('"He said ""hello"""');
    expect(escapeCsvField('"quoted"')).toEqual('"""quoted"""');
  });

  test('text with newlines', () => {
    expect(escapeCsvField('line1\nline2')).toEqual('"line1\nline2"');
    expect(escapeCsvField('text\r\n')).toEqual('"text\r\n"');
  });

  test('text with multiple special characters', () => {
    expect(escapeCsvField('City, "State"\nCountry')).toEqual(
      '"City, ""State""\nCountry"',
    );
  });
});

describe('generateCsv', () => {
  test('writes a header row followed by CRLF separated data rows', () => {
    const csv = generateCsv({
      columns: ['team_number', 'nickname'],
      data: [
        [254, 'The Cheesy Poofs'],
        [1678, 'Citrus Circuits'],
      ],
    });

    expect(csv).toBe(
      'team_number,nickname\r\n254,The Cheesy Poofs\r\n1678,Citrus Circuits',
    );
  });

  test('escapes fields in both the header and the data', () => {
    const csv = generateCsv({
      columns: ['city, state'],
      data: [['San Jose, CA']],
    });

    expect(csv).toBe('"city, state"\r\n"San Jose, CA"');
  });

  test('writes only the header without data', () => {
    expect(generateCsv({ columns: ['a', 'b'], data: [] })).toBe('a,b');
  });
});

describe('downloadCsv', () => {
  const createObjectURL = vi.fn<() => string>(() => 'blob:csv');
  const revokeObjectURL = vi.fn<(url: string) => void>();
  const clickedLinks: Array<{ download: string; href: string }> = [];

  beforeEach(() => {
    clickedLinks.length = 0;
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: createObjectURL,
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: revokeObjectURL,
    });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clickedLinks.push({ download: this.download, href: this.href });
    });
  });

  afterEach(() => {
    Reflect.deleteProperty(URL, 'createObjectURL');
    Reflect.deleteProperty(URL, 'revokeObjectURL');
  });

  test('clicks a download link named after the file', () => {
    downloadCsv('a,b', 'teams.csv');

    expect(clickedLinks).toEqual([{ download: 'teams.csv', href: 'blob:csv' }]);
  });

  test('releases the object url after the download starts', () => {
    downloadCsv('a,b', 'teams.csv');

    expect(revokeObjectURL).toHaveBeenCalledWith('blob:csv');
  });
});

describe('copyCsvToClipboard', () => {
  afterEach(() => {
    Reflect.deleteProperty(navigator, 'clipboard');
  });

  test('writes the csv text to the clipboard', async () => {
    const writeText = vi.fn<(text: string) => Promise<void>>(() =>
      Promise.resolve(),
    );
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });

    await copyCsvToClipboard('a,b');

    expect(writeText).toHaveBeenCalledWith('a,b');
  });

  test('rejects when the clipboard api is unavailable', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: undefined,
    });

    await expect(copyCsvToClipboard('a,b')).rejects.toThrow(
      'Clipboard API not available',
    );
  });
});
