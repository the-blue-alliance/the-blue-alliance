import { Match, MatchAlliance, WltRecord } from '~/api/tba/read';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { median } from '~/lib/utils';

const COMP_LEVEL_SORT_ORDER = {
  f: 5,
  sf: 4,
  qf: 3,
  ef: 2,
  qm: 1,
};

export const COMP_LEVEL_SHORT_STRINGS = {
  f: 'Finals',
  sf: 'Semis',
  qf: 'Quarters',
  ef: 'Eighths',
  qm: 'Quals',
};

export type AllianceColor = 'red' | 'blue';

type RecycleRushWLTStrategy = 'official' | 'score-based';

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

export function matchTitleShort(
  match: Match,
  playoffType: PlayoffType,
): string {
  if (match.comp_level === 'qm' || match.comp_level === 'f') {
    return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.match_number}`;
  }

  // 2023+ double elim brackets
  // 4 team example is 2024micmp
  if (
    playoffType == PlayoffType.DOUBLE_ELIM_4_TEAM ||
    playoffType == PlayoffType.DOUBLE_ELIM_8_TEAM
  ) {
    return `Match ${match.set_number}`;
  }

  // 2015
  if (playoffType == PlayoffType.AVG_SCORE_8_TEAM) {
    return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.match_number}`;
  }

  // 2022 and prior standard single elim
  // round robin also obeys this rule
  // null playoff type is 2022 and prior standard single elim
  // this seems like a reasonable fallback for custom brackets
  return `${COMP_LEVEL_SHORT_STRINGS[match.comp_level]} ${match.set_number} Match ${match.match_number}`;
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

/*
 * Returns the result of a match for a given alliance.
 * @param match - The match to get the result of.
 * @param alliance - The alliance to get the result of.
 * @param recycleRushStrategy - 'official' for quals/qf/sf being all ties. 'score-based' for quals/qf/sf being based on score.
 * @returns 'win', 'loss', 'tie', or undefined if the match hasn't been played.
 */
export function getAllianceMatchResult(
  match: Match,
  alliance: AllianceColor,
  recycleRushStrategy: RecycleRushWLTStrategy,
): 'win' | 'loss' | 'tie' | undefined {
  // match not played or only partially scored
  if (!matchHasBeenPlayed(match)) {
    return undefined;
  }

  // no winner listed
  if (match.winning_alliance === '') {
    // if it's been played, there's no winner, and it's not 2015, it's a tie
    if (!match.key.startsWith('2015')) {
      return 'tie';
    }

    // if it's been played, there's no winner, but it is 2015
    if (recycleRushStrategy === 'official') {
      return 'tie';
    }

    if (recycleRushStrategy === 'score-based') {
      if (
        (match.alliances.red.score > match.alliances.blue.score &&
          alliance === 'red') ||
        (match.alliances.blue.score > match.alliances.red.score &&
          alliance === 'blue')
      ) {
        return 'win';
      }
      if (
        (match.alliances.red.score < match.alliances.blue.score &&
          alliance === 'red') ||
        (match.alliances.blue.score < match.alliances.red.score &&
          alliance === 'blue')
      ) {
        return 'loss';
      }

      return 'tie';
    }
  }

  return match.winning_alliance === alliance ? 'win' : 'loss';
}

export function getTeamMatchResults(
  teamKey: string,
  matches: Match[],
  recycleRushStrategy: RecycleRushWLTStrategy = 'official',
): {
  quals: { wins: Match[]; losses: Match[]; ties: Match[] };
  playoff: { wins: Match[]; losses: Match[]; ties: Match[] };
} {
  const allWins = matches.filter(
    (m) =>
      (getAllianceMatchResult(m, 'red', recycleRushStrategy) === 'win' &&
        m.alliances.red.team_keys.includes(teamKey)) ||
      (getAllianceMatchResult(m, 'blue', recycleRushStrategy) === 'win' &&
        m.alliances.blue.team_keys.includes(teamKey)),
  );
  const allLosses = matches.filter(
    (m) =>
      (getAllianceMatchResult(m, 'red', recycleRushStrategy) === 'loss' &&
        m.alliances.red.team_keys.includes(teamKey)) ||
      (getAllianceMatchResult(m, 'blue', recycleRushStrategy) === 'loss' &&
        m.alliances.blue.team_keys.includes(teamKey)),
  );
  const allTies = matches.filter(
    (m) =>
      (getAllianceMatchResult(m, 'red', recycleRushStrategy) === 'tie' &&
        m.alliances.red.team_keys.includes(teamKey)) ||
      (getAllianceMatchResult(m, 'blue', recycleRushStrategy) === 'tie' &&
        m.alliances.blue.team_keys.includes(teamKey)),
  );
  const quals = {
    wins: allWins.filter((m) => m.comp_level === 'qm'),
    losses: allLosses.filter((m) => m.comp_level === 'qm'),
    ties: allTies.filter((m) => m.comp_level === 'qm'),
  };
  const playoff = {
    wins: allWins.filter((m) => m.comp_level !== 'qm'),
    losses: allLosses.filter((m) => m.comp_level !== 'qm'),
    ties: allTies.filter((m) => m.comp_level !== 'qm'),
  };
  return { quals, playoff };
}

export function calculateTeamRecordsFromMatches(
  teamKey: string,
  matches: Match[],
  recycleRushStrategy: RecycleRushWLTStrategy = 'official',
): {
  quals: WltRecord;
  playoff: WltRecord;
} {
  const { quals, playoff } = getTeamMatchResults(
    teamKey,
    matches,
    recycleRushStrategy,
  );

  const qualsRecord: WltRecord = {
    wins: quals.wins.length,
    losses: quals.losses.length,
    ties: quals.ties.length,
  };

  const playoffRecord: WltRecord = {
    wins: playoff.wins.length,
    losses: playoff.losses.length,
    ties: playoff.ties.length,
  };

  return { quals: qualsRecord, playoff: playoffRecord };
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
