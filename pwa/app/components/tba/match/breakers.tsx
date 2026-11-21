import { CompLevel, Event, Match, PlayoffType } from '~/api/tba/read';
import {
  DOUBLE_ELIM_4_ROUND_MAPPING,
  DOUBLE_ELIM_ROUND_MAPPING,
} from '~/lib/api/PlayoffType';
import { COMP_LEVEL_LONG_STRINGS } from '~/lib/matchUtils';
import { timestampsAreOnDifferentDays } from '~/lib/utils';

export interface BreakerResult {
  shouldBreak: boolean;
  text?: string;
  size?: 'default' | 'small';
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
    size: 'small',
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

const PLAYOFF_START_LABELS = new Map<PlayoffType | null, string>([
  [PlayoffType.DOUBLE_ELIM_8_TEAM, 'Round 1'],
  [PlayoffType.DOUBLE_ELIM_4_TEAM, 'Round 1'],
  [PlayoffType.ROUND_ROBIN_6_TEAM, 'Round Robin'],
  [PlayoffType.CUSTOM, 'Playoffs'],
]);

const DOUBLE_ELIM_ROUNDS = new Map<PlayoffType | null, Map<number, number>>([
  [PlayoffType.DOUBLE_ELIM_8_TEAM, DOUBLE_ELIM_ROUND_MAPPING],
  [PlayoffType.DOUBLE_ELIM_4_TEAM, DOUBLE_ELIM_4_ROUND_MAPPING],
]);

export const START_OF_ELIMS_BREAKER: ShouldInsertBreakCallback = ({
  match,
  matchIndex,
  event,
}) => {
  return {
    shouldBreak: matchIndex === 0 && match.comp_level !== CompLevel.QM,
    text:
      PLAYOFF_START_LABELS.get(event.playoff_type) ??
      COMP_LEVEL_LONG_STRINGS[match.comp_level],
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
  event,
}) => {
  const rounds = DOUBLE_ELIM_ROUNDS.get(event.playoff_type);
  if (!nextMatch || !rounds) {
    return { shouldBreak: false };
  }

  return {
    shouldBreak:
      rounds.get(match.set_number) !== rounds.get(nextMatch.set_number) &&
      nextMatch.comp_level !== CompLevel.F,
    text: `Round ${rounds.get(nextMatch.set_number)}`,
    whereToInsertBreak: 'after',
  };
};
