import { describe, expect, test } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type EventCoprs,
  type Match,
  type MatchAlliance,
  type Media,
  type Team,
} from '~/api/tba/read';
import {
  formatDate,
  formatTime,
  transformCoprsToTable,
  transformMatchesToFlatSchedule,
  transformMatchesToSchedule,
  transformTeamsToTeamList,
} from '~/lib/scoutingUtils';

function makeTeam(overrides: Partial<Team>): Team {
  return {
    key: 'frc254',
    team_number: 254,
    nickname: 'The Cheesy Poofs',
    city: 'San Jose',
    state_prov: 'CA',
    country: 'USA',
    ...overrides,
  } as Team;
}

function alliance(score: number, teamKeys: string[]): MatchAlliance {
  return {
    score,
    team_keys: teamKeys,
    surrogate_team_keys: [],
    dq_team_keys: [],
  };
}

function makeMatch(overrides: Partial<Match> & { key: string }): Match {
  return {
    comp_level: CompLevel.QM,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: alliance(100, ['frc254', 'frc1678', 'frc2056']),
      blue: alliance(80, ['frc1323', 'frc2910', 'frc604']),
    },
    winning_alliance: AllianceColor.RED,
    event_key: overrides.key.split('_')[0],
    time: 1704067200,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
    ...overrides,
  };
}

describe('formatDate', () => {
  test('formats timestamp to YYYY-MM-DD in UTC', () => {
    expect(formatDate(1704067200)).toEqual('2024-01-01');
    expect(formatDate(1609459200)).toEqual('2021-01-01');
    expect(formatDate(0)).toEqual('1970-01-01');
  });

  test('returns empty string for null', () => {
    expect(formatDate(null)).toEqual('');
  });
});

describe('formatTime', () => {
  test('formats timestamp to HH:MM:SS in UTC', () => {
    expect(formatTime(1704067200)).toEqual('00:00:00');
    expect(formatTime(1704110400)).toEqual('12:00:00');
    expect(formatTime(1704153599)).toEqual('23:59:59');
  });

  test('returns empty string for null', () => {
    expect(formatTime(null)).toEqual('');
  });
});

describe('transformTeamsToTeamList', () => {
  test('lists teams in team number order', () => {
    const teams = [
      makeTeam({ key: 'frc1678', team_number: 1678 }),
      makeTeam({ key: 'frc254', team_number: 254 }),
    ];

    const rows = transformTeamsToTeamList(teams, []);

    expect(rows.map((row) => row[0])).toEqual([254, 1678]);
  });

  test('writes a full row without a robot picture', () => {
    const rows = transformTeamsToTeamList([makeTeam({})], []);

    expect(rows).toEqual([
      [254, 'The Cheesy Poofs', 'San Jose', 'CA', 'USA', ''],
    ]);
  });

  test('blanks missing location fields', () => {
    const team = makeTeam({ city: null, state_prov: null, country: null });

    const rows = transformTeamsToTeamList([team], []);

    expect(rows[0].slice(2, 5)).toEqual(['', '', '']);
  });

  test("includes the team's preferred robot picture", () => {
    const media = [
      {
        type: 'imgur',
        foreign_key: 'abc',
        team_keys: ['frc254'],
        preferred: true,
        direct_url: 'https://i.imgur.com/abc.jpg',
        details: {},
      } as Media,
    ];

    const rows = transformTeamsToTeamList([makeTeam({})], media);

    expect(rows[0][5]).toBe('https://i.imgur.com/abc.jpg');
  });
});

describe('transformMatchesToSchedule', () => {
  test('writes one row per match with team numbers and scores', () => {
    const rows = transformMatchesToSchedule([
      makeMatch({ key: '2024test_qm1' }),
    ]);

    expect(rows).toEqual([
      [
        '2024test_qm1',
        '2024-01-01',
        '00:00:00',
        'qm',
        1,
        1,
        254,
        1678,
        2056,
        1323,
        2910,
        604,
        100,
        80,
      ],
    ]);
  });

  test('orders rows by match order', () => {
    const matches = [
      makeMatch({ key: '2024test_qm2', match_number: 2 }),
      makeMatch({ key: '2024test_qm1' }),
    ];

    const rows = transformMatchesToSchedule(matches);

    expect(rows.map((row) => row[0])).toEqual(['2024test_qm1', '2024test_qm2']);
  });

  test('leaves empty alliance slots blank', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: {
        red: alliance(-1, ['frc254']),
        blue: alliance(-1, ['frc1323', 'frc2910']),
      },
    });

    const rows = transformMatchesToSchedule([match]);

    expect(rows[0].slice(6, 12)).toEqual([254, '', '', 1323, 2910, '']);
  });
});

describe('transformMatchesToFlatSchedule', () => {
  test('writes one row per team tagged with its alliance', () => {
    const rows = transformMatchesToFlatSchedule([
      makeMatch({ key: '2024test_qm1' }),
    ]);

    expect(rows).toEqual([
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'red', 254],
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'red', 1678],
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'red', 2056],
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'blue', 1323],
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'blue', 2910],
      ['2024test_qm1', '2024-01-01', '00:00:00', 'qm', 1, 1, 'blue', 604],
    ]);
  });

  test('orders rows by match order', () => {
    const matches = [
      makeMatch({ key: '2024test_sf1m1', comp_level: CompLevel.SF }),
      makeMatch({ key: '2024test_qm1' }),
    ];

    const rows = transformMatchesToFlatSchedule(matches);

    expect(rows.map((row) => row[0])).toEqual([
      '2024test_qm1',
      '2024test_qm1',
      '2024test_qm1',
      '2024test_qm1',
      '2024test_qm1',
      '2024test_qm1',
      '2024test_sf1m1',
      '2024test_sf1m1',
      '2024test_sf1m1',
      '2024test_sf1m1',
      '2024test_sf1m1',
      '2024test_sf1m1',
    ]);
  });
});

describe('transformCoprsToTable', () => {
  test('lists teams by number with values rounded to two decimals', () => {
    const coprs: EventCoprs = {
      totalPoints: { frc1678: 12.346, frc254: 10 },
    };

    expect(transformCoprsToTable(coprs)).toEqual({
      columns: ['team_number', 'totalPoints'],
      data: [
        [254, 10],
        [1678, 12.35],
      ],
    });
  });

  test('drops components that are zero for every team', () => {
    const coprs: EventCoprs = {
      totalPoints: { frc254: 10 },
      unused: { frc254: 0 },
    };

    expect(transformCoprsToTable(coprs).columns).toEqual([
      'team_number',
      'totalPoints',
    ]);
  });

  test('returns only the team column when no component has data', () => {
    const coprs: EventCoprs = { unused: { frc254: 0 } };

    expect(transformCoprsToTable(coprs)).toEqual({
      columns: ['team_number'],
      data: [],
    });
  });

  test('fills a team missing from a component with zero', () => {
    const coprs: EventCoprs = {
      first: { frc1: 1, frc2: 2 },
      second: { frc1: 3 },
    };

    expect(transformCoprsToTable(coprs).data).toEqual([
      [1, 1, 3],
      [2, 2, 0],
    ]);
  });
});
