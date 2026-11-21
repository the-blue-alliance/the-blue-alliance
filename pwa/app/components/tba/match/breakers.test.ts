import { Temporal } from 'temporal-polyfill';
import { describe, expect, test } from 'vitest';

import type { Event, Match } from '~/api/tba/read';
import { CompLevel, PlayoffType } from '~/api/tba/read';
import {
  CHANGE_IN_COMP_LEVEL_BREAKER,
  CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER,
  END_OF_DAY_BREAKER,
  START_OF_ELIMS_BREAKER,
  START_OF_FINALS_BREAKER,
  START_OF_QUALS_BREAKER,
} from '~/components/tba/match/breakers';
import {
  makeEvent as baseEvent,
  makeMatch as baseMatch,
} from '~/test/factories';

function timestamp(isoString: string): number {
  return Temporal.Instant.from(isoString).epochMilliseconds / 1000;
}

function makeMatch(overrides: Partial<Match> = {}): Match {
  return baseMatch({ time: timestamp('2026-03-01T04:30:00Z'), ...overrides });
}

function makeEvent(overrides: Partial<Event> = {}): Event {
  return baseEvent({ playoff_type: PlayoffType.BRACKET_8_TEAM, ...overrides });
}

describe('END_OF_DAY_BREAKER', () => {
  test('does not break when the current match has no scheduled time', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch({ time: null }),
        matchIndex: 0,
        nextMatch: makeMatch(),
        event: makeEvent(),
      }),
    ).toEqual({ shouldBreak: false });
  });

  test('does not break when there is no next match', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }),
    ).toEqual({ shouldBreak: false });
  });

  test('does not break when the next match has no scheduled time', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: makeMatch({ time: null }),
        event: makeEvent(),
      }),
    ).toEqual({ shouldBreak: false });
  });

  test('does not break between matches on the same local day', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch({ time: timestamp('2026-03-01T05:30:00Z') }),
        matchIndex: 0,
        nextMatch: makeMatch({ time: timestamp('2026-03-01T06:00:00Z') }),
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: false,
      text: 'End of Day',
      size: 'small',
      whereToInsertBreak: 'after',
    });
  });

  test('uses the event timezone to detect a new local day', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch({ time: timestamp('2026-03-01T04:30:00Z') }),
        matchIndex: 0,
        nextMatch: makeMatch({ time: timestamp('2026-03-01T05:30:00Z') }),
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: true,
      text: 'End of Day',
      size: 'small',
      whereToInsertBreak: 'after',
    });
  });

  test('falls back to UTC when the event has no timezone', () => {
    expect(
      END_OF_DAY_BREAKER({
        match: makeMatch({ time: timestamp('2026-03-01T23:30:00Z') }),
        matchIndex: 0,
        nextMatch: makeMatch({ time: timestamp('2026-03-02T00:30:00Z') }),
        event: makeEvent({ timezone: null }),
      }),
    ).toEqual({
      shouldBreak: true,
      text: 'End of Day',
      size: 'small',
      whereToInsertBreak: 'after',
    });
  });
});

describe('START_OF_QUALS_BREAKER', () => {
  test('inserts a qualifications label before the first qualification match', () => {
    expect(
      START_OF_QUALS_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: true,
      text: 'Qualifications',
      whereToInsertBreak: 'before',
    });
  });

  test('does not break before a later qualification match', () => {
    expect(
      START_OF_QUALS_BREAKER({
        match: makeMatch(),
        matchIndex: 1,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });

  test('does not break before a playoff match', () => {
    expect(
      START_OF_QUALS_BREAKER({
        match: makeMatch({ comp_level: CompLevel.SF }),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });
});

describe('START_OF_ELIMS_BREAKER', () => {
  test.each([
    [PlayoffType.DOUBLE_ELIM_8_TEAM, CompLevel.SF, 'Round 1'],
    [PlayoffType.DOUBLE_ELIM_4_TEAM, CompLevel.SF, 'Round 1'],
    [PlayoffType.ROUND_ROBIN_6_TEAM, CompLevel.SF, 'Round Robin'],
    [PlayoffType.CUSTOM, CompLevel.QF, 'Playoffs'],
    [PlayoffType.AVG_SCORE_8_TEAM, CompLevel.QF, 'Quarterfinals'],
    [PlayoffType.BRACKET_8_TEAM, CompLevel.QF, 'Quarterfinals'],
    [PlayoffType.BRACKET_16_TEAM, CompLevel.EF, 'Eighthfinals'],
    [PlayoffType.BRACKET_4_TEAM, CompLevel.SF, 'Semifinals'],
    [PlayoffType.BO3_FINALS, CompLevel.F, 'Finals'],
    [null, CompLevel.QF, 'Quarterfinals'],
  ])(
    'labels playoff type %s starting at %s as %s',
    (playoffType, compLevel, expectedText) => {
      expect(
        START_OF_ELIMS_BREAKER({
          match: makeMatch({ comp_level: compLevel }),
          matchIndex: 0,
          nextMatch: null,
          event: makeEvent({ playoff_type: playoffType }),
        }),
      ).toEqual({
        shouldBreak: true,
        text: expectedText,
        whereToInsertBreak: 'before',
      });
    },
  );

  test('does not break before a qualification match', () => {
    expect(
      START_OF_ELIMS_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });

  test('does not break before a later playoff match', () => {
    expect(
      START_OF_ELIMS_BREAKER({
        match: makeMatch({ comp_level: CompLevel.SF }),
        matchIndex: 1,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });
});

describe('START_OF_FINALS_BREAKER', () => {
  test('inserts a finals label before the first final', () => {
    expect(
      START_OF_FINALS_BREAKER({
        match: makeMatch({ comp_level: CompLevel.F }),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: true,
      text: 'Finals',
      whereToInsertBreak: 'before',
    });
  });

  test('does not break before a later final', () => {
    expect(
      START_OF_FINALS_BREAKER({
        match: makeMatch({ comp_level: CompLevel.F }),
        matchIndex: 1,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });

  test('does not break before a non-final match', () => {
    expect(
      START_OF_FINALS_BREAKER({
        match: makeMatch({ comp_level: CompLevel.SF }),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }).shouldBreak,
    ).toBe(false);
  });
});

describe('CHANGE_IN_COMP_LEVEL_BREAKER', () => {
  test('does not break after the final match', () => {
    expect(
      CHANGE_IN_COMP_LEVEL_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }),
    ).toEqual({ shouldBreak: false });
  });

  test('does not break when the competition level stays the same', () => {
    expect(
      CHANGE_IN_COMP_LEVEL_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: makeMatch(),
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: false,
      text: 'Qualifications',
      whereToInsertBreak: 'after',
    });
  });

  test('labels a change with the next competition level', () => {
    expect(
      CHANGE_IN_COMP_LEVEL_BREAKER({
        match: makeMatch({ comp_level: CompLevel.QF }),
        matchIndex: 0,
        nextMatch: makeMatch({ comp_level: CompLevel.SF }),
        event: makeEvent(),
      }),
    ).toEqual({
      shouldBreak: true,
      text: 'Semifinals',
      whereToInsertBreak: 'after',
    });
  });
});

describe('CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER', () => {
  test('does not break after the final match', () => {
    expect(
      CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
        match: makeMatch(),
        matchIndex: 0,
        nextMatch: null,
        event: makeEvent(),
      }),
    ).toEqual({ shouldBreak: false });
  });

  test('does not break between sets in the same round', () => {
    expect(
      CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
        match: makeMatch({ set_number: 1 }),
        matchIndex: 0,
        nextMatch: makeMatch({ set_number: 4 }),
        event: makeEvent({ playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM }),
      }),
    ).toEqual({
      shouldBreak: false,
      text: 'Round 1',
      whereToInsertBreak: 'after',
    });
  });

  test.each([
    [4, 5, 'Round 2'],
    [8, 9, 'Round 3'],
    [10, 11, 'Round 4'],
    [12, 13, 'Round 5'],
  ])(
    'labels the transition from set %s to set %s as %s',
    (setNumber, nextSetNumber, expectedText) => {
      expect(
        CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
          match: makeMatch({ set_number: setNumber }),
          matchIndex: 0,
          nextMatch: makeMatch({ set_number: nextSetNumber }),
          event: makeEvent({ playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM }),
        }),
      ).toEqual({
        shouldBreak: true,
        text: expectedText,
        whereToInsertBreak: 'after',
      });
    },
  );

  test('does not insert a round break before finals', () => {
    expect(
      CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
        match: makeMatch({ set_number: 12 }),
        matchIndex: 0,
        nextMatch: makeMatch({ comp_level: CompLevel.F, set_number: 1 }),
        event: makeEvent({ playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM }),
      }).shouldBreak,
    ).toBe(false);
  });

  test.each([
    [2, 3, 'Round 2'],
    [4, 5, 'Round 3'],
  ])(
    'labels the 4-team transition from set %s to set %s as %s',
    (setNumber, nextSetNumber, expectedText) => {
      expect(
        CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
          match: makeMatch({ set_number: setNumber }),
          matchIndex: 0,
          nextMatch: makeMatch({ set_number: nextSetNumber }),
          event: makeEvent({ playoff_type: PlayoffType.DOUBLE_ELIM_4_TEAM }),
        }),
      ).toEqual({
        shouldBreak: true,
        text: expectedText,
        whereToInsertBreak: 'after',
      });
    },
  );

  test('does not break between sets of a single-elimination bracket', () => {
    expect(
      CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER({
        match: makeMatch({ comp_level: CompLevel.EF, set_number: 4 }),
        matchIndex: 0,
        nextMatch: makeMatch({ comp_level: CompLevel.EF, set_number: 5 }),
        event: makeEvent({ playoff_type: PlayoffType.BRACKET_16_TEAM }),
      }),
    ).toEqual({ shouldBreak: false });
  });
});
