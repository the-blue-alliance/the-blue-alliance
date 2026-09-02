import { Temporal } from 'temporal-polyfill';
import { describe, expect, test } from 'vitest';

import { getKickoffCountdownTarget } from '~/lib/kickoffUtils';

const KICKOFF_2027 = '2027-01-09T17:00:00+00:00';
const KICKOFF_2026 = '2026-01-10T17:00:00+00:00';

const at = (s: string) => Temporal.Instant.from(s);

describe.concurrent('getKickoffCountdownTarget', () => {
  test.each([undefined, ''])('returns null for %o', (value) => {
    expect(getKickoffCountdownTarget(value, at('2026-12-15T12:00:00Z'))).toBe(
      null,
    );
  });

  test('returns null for an unparseable datetime', () => {
    expect(
      getKickoffCountdownTarget('not a datetime', at('2026-12-15T12:00:00Z')),
    ).toBe(null);
  });

  test('returns the kickoff in Eastern time during the window', () => {
    const target = getKickoffCountdownTarget(
      KICKOFF_2027,
      at('2026-12-15T12:00:00Z'),
    );

    expect(target).not.toBe(null);
    expect(target?.timeZoneId).toBe('America/New_York');
    expect(target?.toPlainDateTime().toString()).toBe('2027-01-09T12:00:00');
  });

  test('returns null in September, before the window opens', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2026-09-02T12:00:00Z')),
    ).toBe(null);
  });

  test('returns null an hour before November 1st Eastern', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2026-10-31T23:00:00-04:00')),
    ).toBe(null);
  });

  test('returns the kickoff exactly at November 1st Eastern', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2026-11-01T00:00:00-04:00')),
    ).not.toBe(null);
  });

  test('returns the kickoff while kickoff is happening', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2027-01-09T17:30:00Z')),
    ).not.toBe(null);
  });

  test('returns the kickoff 23 hours after kickoff', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2027-01-10T16:00:00Z')),
    ).not.toBe(null);
  });

  test('returns null 25 hours after kickoff', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2027, at('2027-01-10T18:00:00Z')),
    ).toBe(null);
  });

  test('returns null for a kickoff that already passed', () => {
    expect(
      getKickoffCountdownTarget(KICKOFF_2026, at('2026-12-15T12:00:00Z')),
    ).toBe(null);
  });
});
