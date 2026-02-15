import { describe, expect, test } from 'vitest';

import { escapeCsvField } from '~/lib/csvUtils';

describe.concurrent('escapeCsvField', () => {
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
