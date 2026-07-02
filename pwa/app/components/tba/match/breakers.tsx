import { CompLevel, Event, Match, PlayoffType } from '~/api/tba/read';
import { DOUBLE_ELIM_ROUND_MAPPING } from '~/lib/api/PlayoffType';
import { COMP_LEVEL_LONG_STRINGS } from '~/lib/matchUtils';
import { timestampsAreOnDifferentDays } from '~/lib/utils';

export interface BreakerResult {
  shouldBreak: boolean;
  text?: string;
  whereToInsertBreak?: 'before' | 'after';
}

export type ShouldInsertBreakCallback = (params: {
  match: Match;
  matchIndex: number;
  nextMatch: Match | null;
  event: Event;
}) => BreakerResult;

export const END_OF_DAY_BREAKER: ShouldInsertBreakCallback = ({
  match,
  nextMatch,
  event,
}) => {
  if (!match.time || !nextMatch?.time) {
    return { shouldBreak: false };
  }

  return {
    shouldBreak: timestampsAreOnDifferentDays(
      match.time,
      nextMatch.time,
      event.timezone ?? 'UTC',
    ),
    text: 'End of Day',
    whereToInsertBreak: 'after',
  };
};

export const START_OF_QUALS_BREAKER: ShouldInsertBreakCallback = ({
  match,
  matchIndex,
}) => {
  return {
    shouldBreak: matchIndex === 0 && match.comp_level === CompLevel.QM,
    text: COMP_LEVEL_LONG_STRINGS[CompLevel.QM],
    whereToInsertBreak: 'before',
  };
};

export const START_OF_ELIMS_BREAKER: ShouldInsertBreakCallback = ({
  match,
  matchIndex,
  event,
}) => {
  return {
    shouldBreak: matchIndex === 0 && match.comp_level !== CompLevel.QM,
    text: (
      {
        [PlayoffType.DOUBLE_ELIM_8_TEAM]: 'Round 1',
        [PlayoffType.AVG_SCORE_8_TEAM]: COMP_LEVEL_LONG_STRINGS[CompLevel.QF],
        [PlayoffType.BRACKET_8_TEAM]: COMP_LEVEL_LONG_STRINGS[CompLevel.QF],
        [PlayoffType.CUSTOM]: 'Playoffs',
      } as Partial<Record<PlayoffType, string>>
    )[event.playoff_type ?? PlayoffType.BRACKET_8_TEAM],
    whereToInsertBreak: 'before',
  };
};

export const START_OF_FINALS_BREAKER: ShouldInsertBreakCallback = ({
  match,
  matchIndex,
}) => {
  return {
    shouldBreak: matchIndex === 0 && match.comp_level === CompLevel.F,
    text: COMP_LEVEL_LONG_STRINGS[CompLevel.F],
    whereToInsertBreak: 'before',
  };
};

export const CHANGE_IN_COMP_LEVEL_BREAKER: ShouldInsertBreakCallback = ({
  match,
  nextMatch,
}) => {
  if (!nextMatch) {
    return { shouldBreak: false };
  }

  return {
    shouldBreak: match.comp_level !== nextMatch.comp_level,
    text: COMP_LEVEL_LONG_STRINGS[nextMatch.comp_level],
    whereToInsertBreak: 'after',
  };
};

export const CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER: ShouldInsertBreakCallback = ({
  match,
  nextMatch,
}) => {
  if (!nextMatch) {
    return { shouldBreak: false };
  }

  return {
    shouldBreak:
      DOUBLE_ELIM_ROUND_MAPPING.get(match.set_number) !==
        DOUBLE_ELIM_ROUND_MAPPING.get(nextMatch.set_number) &&
      nextMatch.comp_level !== CompLevel.F,
    text: `Round ${DOUBLE_ELIM_ROUND_MAPPING.get(nextMatch.set_number)}`,
    whereToInsertBreak: 'after',
  };
};
