import { Event, Match, MatchAlliance, WltRecord } from '~/api/tba/read';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { median } from '~/lib/utils';

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

export function isValidMatchKey(key: string) {
  return /^[1-9]\d{3}[a-z]+[0-9]*_(?:qm|ef\d{1,2}m|qf\d{1,2}m|sf\d{1,2}m|f\dm)\d+$/.test(
    key,
  );
}

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

function getMaybeUnpenalizedScores(m: Match): { blue: number; red: number } {
  if (m.score_breakdown === null) {
    return { blue: m.alliances.blue.score, red: m.alliances.red.score };
  }

  // 2015 used snake_case
  if (
    'foul_points' in m.score_breakdown.red &&
    'foul_points' in m.score_breakdown.blue
  ) {
    return {
      blue: m.alliances.blue.score - (m.score_breakdown.blue.foul_points ?? 0),
      red: m.alliances.red.score - (m.score_breakdown.red.foul_points ?? 0),
    };
  }

  // 2016+ uses camelCase
  if (
    'foulPoints' in m.score_breakdown.red &&
    'foulPoints' in m.score_breakdown.blue
  ) {
    return {
      blue: m.alliances.blue.score - (m.score_breakdown.blue.foulPoints ?? 0),
      red: m.alliances.red.score - (m.score_breakdown.red.foulPoints ?? 0),
    };
  }

  // uhh, this shouldn't happen, but...
  return { blue: m.alliances.blue.score, red: m.alliances.red.score };
}

export function calculateTeamRecordsFromMatches(
  teamKey: string,
  matches: Match[],
): {
  quals: WltRecord;
  playoff: WltRecord;
} {
  const won = matches.filter(
    (m) =>
      (m.winning_alliance === 'red' &&
        m.alliances.red.team_keys.includes(teamKey)) ||
      (m.winning_alliance === 'blue' &&
        m.alliances.blue.team_keys.includes(teamKey)),
  );

  const lost = matches.filter(
    (m) =>
      (m.winning_alliance === 'red' &&
        m.alliances.blue.team_keys.includes(teamKey)) ||
      (m.winning_alliance === 'blue' &&
        m.alliances.red.team_keys.includes(teamKey)),
  );

  const tied = matches.filter(
    (m) =>
      (m.alliances.blue.team_keys.includes(teamKey) ||
        m.alliances.red.team_keys.includes(teamKey)) &&
      m.winning_alliance === '' &&
      matchHasBeenPlayed(m),
  );

  const quals: WltRecord = {
    wins: won.filter((m) => m.comp_level === 'qm').length,
    losses: lost.filter((m) => m.comp_level === 'qm').length,
    ties: tied.filter((m) => m.comp_level === 'qm').length,
  };

  const playoff: WltRecord = {
    wins: won.filter((m) => m.comp_level !== 'qm').length,
    losses: lost.filter((m) => m.comp_level !== 'qm').length,
    ties: tied.filter((m) => m.comp_level !== 'qm').length,
  };

  return { quals, playoff };
}

export function getTeamsUnpenalizedHighScore(
  teamKey: string,
  matches: Match[],
):
  | {
      match: Match;
      score: number;
      alliance: MatchAlliance;
    }
  | undefined {
  if (matches.length === 0) {
    return undefined;
  }

  const matchesWithTeam = matches.filter(
    (m) =>
      m.alliances.red.team_keys.includes(teamKey) ||
      m.alliances.blue.team_keys.includes(teamKey),
  );

  if (matchesWithTeam.length === 0) {
    return undefined;
  }

  const highScoreMatch = matchesWithTeam
    .map((m) => {
      const unpenalized = getMaybeUnpenalizedScores(m);

      if (m.alliances.red.team_keys.includes(teamKey)) {
        return {
          match: m,
          score: unpenalized.red,
          alliance: m.alliances.red,
        };
      }

      return {
        match: m,
        score: unpenalized.blue,
        alliance: m.alliances.blue,
      };
    })
    .sort((a, b) => b.score - a.score)[0];

  return highScoreMatch;
}

export function getHighScoreMatch(matches: Match[]): Match | undefined {
  if (matches.length === 0) {
    return undefined;
  }

  const scores = matches.map((m) => ({
    match: m,
    score: Math.max(m.alliances.red.score, m.alliances.blue.score),
  }));

  scores.sort((a, b) => b.score - a.score);

  return scores[0].match;
}

export function calculateMedianTurnaroundTime(
  matches: Match[],
): number | undefined {
  const turnarounds = [];

  for (let i = 1; i < matches.length; i++) {
    const currTime = matches[i].actual_time;
    const prevTime = matches[i - 1].actual_time;

    if (currTime !== null && prevTime !== null) {
      turnarounds.push(currTime - prevTime);
    }
  }

  turnarounds.sort((a, b) => a - b);
  return median(turnarounds);
}
