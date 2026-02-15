import { describe, expect, test } from 'vitest';

import { formatDate, formatTime } from '~/lib/scoutingUtils';

describe.concurrent('formatDate', () => {
  test('formats timestamp to YYYY-MM-DD in UTC', () => {
    expect(formatDate(1704067200)).toEqual('2024-01-01');
    expect(formatDate(1609459200)).toEqual('2021-01-01');
    expect(formatDate(0)).toEqual('1970-01-01');
  });

  test('returns empty string for null', () => {
    expect(formatDate(null)).toEqual('');
  });
});

describe.concurrent('formatTime', () => {
  test('formats timestamp to HH:MM:SS in UTC', () => {
    expect(formatTime(1704067200)).toEqual('00:00:00');
    expect(formatTime(1704110400)).toEqual('12:00:00');
    expect(formatTime(1704153599)).toEqual('23:59:59');
  });

  test('returns empty string for null', () => {
    expect(formatTime(null)).toEqual('');
  });
});
