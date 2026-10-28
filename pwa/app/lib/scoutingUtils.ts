import { EventCoprs, Match, Media, Team } from '~/api/tba/read';
import { sortMatchComparator } from '~/lib/matchUtils';
import { getTeamPreferredRobotPicMedium } from '~/lib/mediaUtils';
import { MatchScoreBreakdownAlliance } from '~/lib/rankingPoints';
import {
  ROBOT_ACTIONS,
  RobotActionName,
  STATIONS,
  Station,
  getRobotScore,
  getUnscoredRobotFields,
} from '~/lib/robotScoring';

function extractTeamNumber(teamKey: string): number {
  return parseInt(teamKey.replace(/^frc/, ''), 10);
}

export function formatDate(timestamp: number | null): string {
  if (timestamp === null) {
    return '';
  }

  const date = new Date(timestamp * 1000);
  const formatter = new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'UTC',
  });

  const parts = formatter.formatToParts(date);
  const year = parts.find((p) => p.type === 'year')?.value ?? '';
  const month = parts.find((p) => p.type === 'month')?.value ?? '';
  const day = parts.find((p) => p.type === 'day')?.value ?? '';

  return `${year}-${month}-${day}`;
}

export function formatTime(timestamp: number | null): string {
  if (timestamp === null) {
    return '';
  }

  const date = new Date(timestamp * 1000);
  const formatter = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'UTC',
  });

  const parts = formatter.formatToParts(date);
  const hour = parts.find((p) => p.type === 'hour')?.value ?? '';
  const minute = parts.find((p) => p.type === 'minute')?.value ?? '';
  const second = parts.find((p) => p.type === 'second')?.value ?? '';

  return `${hour}:${minute}:${second}`;
}

export function transformTeamsToTeamList(
  teams: Team[],
  allMedia: Media[],
): (string | number)[][] {
  const sortedTeams = [...teams].sort((a, b) => a.team_number - b.team_number);

  return sortedTeams.map((team) => {
    const teamMedia = allMedia.filter((m) => m.team_keys.includes(team.key));
    const robotPicUrl = getTeamPreferredRobotPicMedium(teamMedia) ?? '';

    return [
      team.team_number,
      team.nickname ?? '',
      team.city ?? '',
      team.state_prov ?? '',
      team.country ?? '',
      robotPicUrl,
    ];
  });
}

export function transformMatchesToSchedule(
  matches: Match[],
): (string | number)[][] {
  const sortedMatches = [...matches].sort(sortMatchComparator);

  return sortedMatches.map((match) => {
    const red1 = match.alliances.red.team_keys[0]
      ? extractTeamNumber(match.alliances.red.team_keys[0])
      : '';
    const red2 = match.alliances.red.team_keys[1]
      ? extractTeamNumber(match.alliances.red.team_keys[1])
      : '';
    const red3 = match.alliances.red.team_keys[2]
      ? extractTeamNumber(match.alliances.red.team_keys[2])
      : '';
    const blue1 = match.alliances.blue.team_keys[0]
      ? extractTeamNumber(match.alliances.blue.team_keys[0])
      : '';
    const blue2 = match.alliances.blue.team_keys[1]
      ? extractTeamNumber(match.alliances.blue.team_keys[1])
      : '';
    const blue3 = match.alliances.blue.team_keys[2]
      ? extractTeamNumber(match.alliances.blue.team_keys[2])
      : '';

    return [
      match.key,
      formatDate(match.time),
      formatTime(match.time),
      match.comp_level,
      match.match_number,
      match.set_number,
      red1,
      red2,
      red3,
      blue1,
      blue2,
      blue3,
      match.alliances.red.score,
      match.alliances.blue.score,
    ];
  });
}

export function transformMatchesToFlatSchedule(
  matches: Match[],
): (string | number)[][] {
  const sortedMatches = [...matches].sort(sortMatchComparator);
  const rows: (string | number)[][] = [];

  for (const match of sortedMatches) {
    const baseData = [
      match.key,
      formatDate(match.time),
      formatTime(match.time),
      match.comp_level,
      match.match_number,
      match.set_number,
    ];

    for (const teamKey of match.alliances.red.team_keys) {
      rows.push([...baseData, 'red', extractTeamNumber(teamKey)]);
    }

    for (const teamKey of match.alliances.blue.team_keys) {
      rows.push([...baseData, 'blue', extractTeamNumber(teamKey)]);
    }
  }

  return rows;
}

const ROBOT_ACTION_COLUMNS: Record<RobotActionName, string> = {
  leave: 'leave',
  autoClimb: 'auto_climb',
  endgame: 'endgame',
};

function robotCells(
  year: number,
  alliance: MatchScoreBreakdownAlliance,
  station: Station,
): Record<string, string | number> {
  const score = getRobotScore(year, alliance, station);
  if (score === undefined) {
    return getUnscoredRobotFields(alliance, station);
  }

  return Object.fromEntries(
    ROBOT_ACTIONS.flatMap((name) => {
      const action = score[name];
      const column = ROBOT_ACTION_COLUMNS[name];
      return action
        ? [
            [column, action.result],
            [`${column}_points`, action.points],
          ]
        : [];
    }),
  );
}

export function transformMatchesToRobotBreakdown(matches: Match[]): {
  columns: string[];
  data: (string | number)[][];
} {
  const baseColumns = [
    'match_key',
    'comp_level',
    'set_number',
    'match_number',
    'color',
    'station',
    'team',
  ];
  const robots: {
    base: (string | number)[];
    cells: Record<string, string | number>;
  }[] = [];

  for (const match of [...matches].sort(sortMatchComparator)) {
    if (match.score_breakdown === null) {
      continue;
    }

    const year = Number(match.key.slice(0, 4));

    for (const color of ['red', 'blue'] as const) {
      for (const station of STATIONS) {
        const teamKey = match.alliances[color].team_keys[station - 1];
        robots.push({
          base: [
            match.key,
            match.comp_level,
            match.set_number,
            match.match_number,
            color,
            station,
            teamKey ? extractTeamNumber(teamKey) : '',
          ],
          cells: robotCells(year, match.score_breakdown[color], station),
        });
      }
    }
  }

  const robotColumns = [
    ...new Set(robots.flatMap(({ cells }) => Object.keys(cells))),
  ];
  if (robotColumns.length === 0) {
    return { columns: baseColumns, data: [] };
  }

  return {
    columns: [...baseColumns, ...robotColumns],
    data: robots.map(({ base, cells }) => [
      ...base,
      ...robotColumns.map((column) => cells[column] ?? ''),
    ]),
  };
}

export function transformCoprsToTable(coprs: EventCoprs): {
  columns: string[];
  data: (string | number)[][];
} {
  const componentNames = Object.keys(coprs).filter((componentName) => {
    const values = Object.values(coprs[componentName]);
    return values.some((v) => v !== 0);
  });

  if (componentNames.length === 0) {
    return { columns: ['team_number'], data: [] };
  }

  const teamKeys = Object.keys(coprs[componentNames[0]]);
  const sortedTeamKeys = teamKeys.sort((a, b) => {
    const numA = extractTeamNumber(a);
    const numB = extractTeamNumber(b);
    return numA - numB;
  });

  const columns = ['team_number', ...componentNames];
  const data = sortedTeamKeys.map((teamKey) => {
    const teamNumber = extractTeamNumber(teamKey);
    const row: (string | number)[] = [teamNumber];

    for (const componentName of componentNames) {
      const value = coprs[componentName][teamKey] ?? 0;
      row.push(Math.round(value * 100) / 100);
    }

    return row;
  });

  return { columns, data };
}
