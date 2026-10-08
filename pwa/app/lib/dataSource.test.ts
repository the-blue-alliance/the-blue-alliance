import { describe, expect, test } from 'vitest';

import { getDataSource, setDataSource } from '~/lib/dataSource';
import { getDisplayName, getInitials } from '~/lib/profileUtils';

function fakeStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
  };
}

// import.meta.env.DEV is true under vitest, so the dev-only gate is open here
describe.concurrent('dataSource', () => {
  test('defaults to prod', () => {
    expect(getDataSource(fakeStorage())).toBe('prod');
  });

  test('reads a stored local preference', () => {
    expect(getDataSource(fakeStorage({ 'tba-data-source': 'local' }))).toBe(
      'local',
    );
  });

  test('ignores garbage values', () => {
    expect(getDataSource(fakeStorage({ 'tba-data-source': 'nonsense' }))).toBe(
      'prod',
    );
  });

  test('round-trips through setDataSource', () => {
    const storage = fakeStorage();
    setDataSource('local', storage);
    expect(getDataSource(storage)).toBe('local');
    setDataSource('prod', storage);
    expect(getDataSource(storage)).toBe('prod');
  });

  test('prod on the server (no storage)', () => {
    expect(getDataSource(undefined)).toBe('prod');
  });
});

describe.concurrent('getInitials', () => {
  test('two-word names use first and last initials', () => {
    expect(getInitials('Greg Marra', null)).toBe('GM');
    expect(getInitials('Ada Byron Lovelace', null)).toBe('AL');
  });

  test('single names use one initial', () => {
    expect(getInitials('greg', null)).toBe('G');
  });

  test('falls back to email, then ?', () => {
    expect(getInitials(null, 'moderator@example.com')).toBe('M');
    expect(getInitials('', '')).toBe('?');
    expect(getInitials(undefined, undefined)).toBe('?');
  });
});

describe.concurrent('getDisplayName', () => {
  test('uses the display name when present', () => {
    expect(getDisplayName({ displayName: 'Greg Marra' })).toBe('Greg Marra');
  });

  test('falls back for missing or blank names', () => {
    expect(getDisplayName({ displayName: null })).toBe('TBA Account');
    expect(getDisplayName({ displayName: '  ' })).toBe('TBA Account');
  });
});
