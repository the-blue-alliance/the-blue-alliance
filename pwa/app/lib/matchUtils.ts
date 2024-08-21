import { Event, Match, WltRecord } from '~/api/v3';
import { PlayoffType } from '~/lib/api/PlayoffType';

const COMP_LEVEL_SORT_ORDER = {
  f: 5,
  sf: 4,
  qf: 3,
  ef: 2,
  qm: 1,
};

const COMP_LEVEL_SHORT_STRINGS = {
  f: 'Finals',
  sf: 'Semis',
  qf: 'Quarters',
  ef: 'Eighths',
  qm: 'Quals',
};

export function sortMatchComparator(a: Match, b: Match) {
  if (a.comp_level !== b.comp_level) {
    return (
      COMP_LEVEL_SORT_ORDER[a.comp_level] - COMP_LEVEL_SORT_ORDER[b.comp_level]
    );
  }
  return a.set_number - b.set_number || a.match_number - b.match_number;
}

export function matchTitleShort(match: Match, event: Event): string {
  if (match.comp_level === 'qm' || match.comp_level === 'f') {
    return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.match_number}`;
  }

  // 2023+ double elim brackets
  // 4 team example is 2024micmp
  if (
    event.playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM ||
    event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM
  ) {
    return `Match ${match.set_number}`;
  }

  // 2015
  if (event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM) {
    return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.match_number}`;
  }

  // 2022 and prior standard single elim
  // round robin also obeys this rule
  // null playoff type is 2022 and prior standard single elim
  // this seems like a reasonable fallback for custom brackets
  if (
    [
      PlayoffType.BRACKET_2_TEAM,
      PlayoffType.BRACKET_4_TEAM,
      PlayoffType.BRACKET_8_TEAM,
      PlayoffType.BRACKET_16_TEAM,
      PlayoffType.ROUND_ROBIN_6_TEAM,
      PlayoffType.CUSTOM,
      null,
    ].includes(event.playoff_type)
  ) {
    return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.set_number} Match ${match.match_number}`;
  }

  // todo later in development: replace this with reasonable fallback
  console.log(match.key, event);
  return 'IF YOU SEE THIS PLEASE PING JUSTIN/EUGENE WITH EVENT KEY';
}

function matchHasBeenPlayed(match: Match) {
  return match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;
}

export function calculateTeamRecordFromMatches(
  teamKey: string,
  matches: Match[],
): WltRecord {
  const won = matches.filter(
    (m) =>
      (m.winning_alliance === 'red' &&
        m.alliances.red.team_keys.includes(teamKey)) ||
      (m.winning_alliance === 'blue' &&
        m.alliances.blue.team_keys.includes(teamKey)),
  ).length;

  const lost = matches.filter(
    (m) =>
      (m.winning_alliance === 'red' &&
        m.alliances.blue.team_keys.includes(teamKey)) ||
      (m.winning_alliance === 'blue' &&
        m.alliances.red.team_keys.includes(teamKey)),
  ).length;

  const tied = matches.filter(
    (m) =>
      (m.alliances.blue.team_keys.includes(teamKey) ||
        m.alliances.red.team_keys.includes(teamKey)) &&
      m.winning_alliance === '' &&
      matchHasBeenPlayed(m),
  ).length;

  return { wins: won, losses: lost, ties: tied };
}
