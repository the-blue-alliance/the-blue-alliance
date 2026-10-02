import { describe, expect, test } from 'vitest';

import type { Event, Match, MatchAlliance } from '~/api/tba/read';
import {
  AllianceColor,
  CompLevel,
  EventType,
  PlayoffType,
} from '~/api/tba/read';
import {
  calculateTeamRecordsFromMatches,
  formatMatchKeyName,
  formatMatchTime,
  getAllianceMatchResult,
  getMatchScoreWithoutAdjustPoints,
  getTeamMatchResults,
  getTeamsUnpenalizedHighScore,
  isValidMatchKey,
  matchHasBeenPlayed,
  matchTitleShort,
  parseMatchKey,
  sortMatchComparator,
  sortMultipleEventsMatches,
} from '~/lib/matchUtils';

describe('isValidMatchKey', () => {
  test.each([
    '2019nyny_qm1',
    '2010ct_sf1m3',
    '2022on306_qm15',
    '2023week0_sf13m1',
    '2023bc_ef10m1',
    '2023bc_qf10m1',
  ])('valid match key', (key) => {
    expect(isValidMatchKey(key)).toBe(true);
  });

  test.each([
    'frc177',
    '2010ct_qm1m1',
    '2010ctf1m1',
    '2010ct_f1',
    '2022on_306_qm15',
    '2023week0_sf130m1',
    '2023bc_f10m1',
    '2023bc_ef123m1',
    '2023bc_qf123m1',
  ])('invalid match key', (key) => {
    expect(isValidMatchKey(key)).toBe(false);
  });
});

describe('getAllianceMatchResult', () => {
  // Helper function to create a mock match
  function createMockMatch(
    key: string,
    redScore: number,
    blueScore: number,
    winningAlliance: AllianceColor,
  ): Match {
    return {
      key,
      comp_level: CompLevel.QM,
      set_number: 1,
      match_number: 1,
      alliances: {
        red: {
          score: redScore,
          team_keys: ['frc254', 'frc1678', 'frc2056'],
          surrogate_team_keys: [],
          dq_team_keys: [],
        },
        blue: {
          score: blueScore,
          team_keys: ['frc1323', 'frc2910', 'frc604'],
          surrogate_team_keys: [],
          dq_team_keys: [],
        },
      },
      winning_alliance: winningAlliance,
      event_key: key.split('_')[0],
      time: null,
      actual_time: null,
      predicted_time: null,
      post_result_time: null,
      score_breakdown: null,
      videos: [],
    };
  }

  test('returns undefined when match has not been played', () => {
    const match = createMockMatch(
      '2024test_qm1',
      -1,
      -1,
      AllianceColor.NO_ALLIANCE,
    );
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'official'),
    ).toBeUndefined();
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'official'),
    ).toBeUndefined();
  });

  test('returns win when alliance won', () => {
    const match = createMockMatch('2024test_qm1', 100, 80, AllianceColor.RED);
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'win',
    );
  });

  test('returns loss when alliance lost', () => {
    const match = createMockMatch('2024test_qm1', 100, 80, AllianceColor.RED);
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'loss',
    );
  });

  test('returns tie when match is tied (non-2015)', () => {
    const match = createMockMatch(
      '2024test_qm1',
      100,
      100,
      AllianceColor.NO_ALLIANCE,
    );
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'tie',
    );
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'tie',
    );
  });

  test('returns tie for 2015 match with official strategy', () => {
    const match = createMockMatch(
      '2015test_qm1',
      100,
      80,
      AllianceColor.NO_ALLIANCE,
    );
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'tie',
    );
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'tie',
    );
  });

  test('returns win/loss for 2015 match with score-based strategy when red scores higher', () => {
    const match = createMockMatch(
      '2015test_qm1',
      100,
      80,
      AllianceColor.NO_ALLIANCE,
    );
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('win');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('loss');
  });

  test('returns win/loss for 2015 match with score-based strategy when blue scores higher', () => {
    const match = createMockMatch(
      '2015test_qm1',
      80,
      100,
      AllianceColor.NO_ALLIANCE,
    );
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('loss');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('win');
  });

  test('returns tie for 2015 match with score-based strategy when scores are equal', () => {
    const match = createMockMatch(
      '2015test_qm1',
      100,
      100,
      AllianceColor.NO_ALLIANCE,
    );
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('tie');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('tie');
  });

  test('handles blue alliance winning', () => {
    const match = createMockMatch('2024test_qm1', 80, 100, AllianceColor.BLUE);
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'win',
    );
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'loss',
    );
  });

  test('handles different comp levels', () => {
    const qualsMatch = createMockMatch(
      '2024test_qm1',
      100,
      80,
      AllianceColor.RED,
    );
    qualsMatch.comp_level = CompLevel.QM;
    expect(
      getAllianceMatchResult(qualsMatch, AllianceColor.RED, 'official'),
    ).toBe('win');

    const finalsMatch = createMockMatch(
      '2024test_f1m1',
      100,
      80,
      AllianceColor.RED,
    );
    finalsMatch.comp_level = CompLevel.F;
    expect(
      getAllianceMatchResult(finalsMatch, AllianceColor.RED, 'official'),
    ).toBe('win');
  });

  test('handles 2015 playoff matches with score-based strategy', () => {
    const match = createMockMatch(
      '2015test_sf1m1',
      100,
      80,
      AllianceColor.NO_ALLIANCE,
    );
    match.comp_level = CompLevel.SF;
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('win');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('loss');
  });
});

describe('parseMatchKey', () => {
  test('parses playoff keys with a set number', () => {
    expect(parseMatchKey('2026arc_sf3m1')).toEqual({
      eventKey: '2026arc',
      compLevel: CompLevel.SF,
      setNumber: 3,
      matchNumber: 1,
    });
  });

  test('parses qualification keys with an implied set of 1', () => {
    expect(parseMatchKey('2026gal_qm87')).toEqual({
      eventKey: '2026gal',
      compLevel: CompLevel.QM,
      setNumber: 1,
      matchNumber: 87,
    });
  });

  test('rejects malformed keys', () => {
    expect(parseMatchKey('frc254')).toBeNull();
    expect(parseMatchKey('2026arc_xx1')).toBeNull();
  });
});

describe('formatMatchKeyName', () => {
  const archimedes = {
    event_type: EventType.CMP_DIVISION,
    year: 2026,
    city: 'Houston',
    short_name: 'Archimedes',
    name: 'Archimedes Division',
    playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
  };

  test('double-elim playoff match', () => {
    expect(formatMatchKeyName('2026arc_sf3m1', archimedes)).toBe(
      'Archimedes Division Match 3',
    );
  });

  test('qualification match', () => {
    expect(formatMatchKeyName('2026arc_qm87', archimedes)).toBe(
      'Archimedes Division Quals 87',
    );
  });

  test('finals', () => {
    expect(formatMatchKeyName('2026arc_f1m2', archimedes)).toBe(
      'Archimedes Division Finals 2',
    );
  });

  test('legacy single-elim bracket names the set and match', () => {
    expect(
      formatMatchKeyName('2019casj_sf2m3', {
        ...archimedes,
        year: 2019,
        event_type: EventType.REGIONAL,
        short_name: 'Silicon Valley',
        playoff_type: PlayoffType.BRACKET_8_TEAM,
      }),
    ).toBe('Silicon Valley Regional Semis 2 Match 3');
  });

  test('without the event, just the match title; unparseable keys pass through', () => {
    expect(formatMatchKeyName('2026arc_qm87')).toBe('Quals 87');
    expect(formatMatchKeyName('garbage')).toBe('garbage');
  });
});

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
      red: alliance(-1, ['frc254', 'frc1678', 'frc2056']),
      blue: alliance(-1, ['frc1323', 'frc2910', 'frc604']),
    },
    winning_alliance: AllianceColor.NO_ALLIANCE,
    event_key: overrides.key.split('_')[0],
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
    ...overrides,
  };
}

function breakdown(
  red: Record<string, number>,
  blue: Record<string, number>,
): Match['score_breakdown'] {
  return { red, blue } as unknown as Match['score_breakdown'];
}

describe('sortMatchComparator', () => {
  test('orders qualification matches before playoff matches', () => {
    const matches = [
      makeMatch({ key: '2024test_f1m1', comp_level: CompLevel.F }),
      makeMatch({
        key: '2024test_sf2m1',
        comp_level: CompLevel.SF,
        set_number: 2,
      }),
      makeMatch({ key: '2024test_qm9', match_number: 9 }),
    ];

    const keys = matches.sort(sortMatchComparator).map((m) => m.key);

    expect(keys).toEqual(['2024test_qm9', '2024test_sf2m1', '2024test_f1m1']);
  });

  test('orders by set number then match number within a level', () => {
    const matches = [
      makeMatch({
        key: '2024test_sf2m1',
        comp_level: CompLevel.SF,
        set_number: 2,
        match_number: 1,
      }),
      makeMatch({
        key: '2024test_sf1m2',
        comp_level: CompLevel.SF,
        set_number: 1,
        match_number: 2,
      }),
      makeMatch({
        key: '2024test_sf1m1',
        comp_level: CompLevel.SF,
        set_number: 1,
        match_number: 1,
      }),
    ];

    const keys = matches.sort(sortMatchComparator).map((m) => m.key);

    expect(keys).toEqual([
      '2024test_sf1m1',
      '2024test_sf1m2',
      '2024test_sf2m1',
    ]);
  });
});

describe('sortMultipleEventsMatches', () => {
  test('groups matches by the given event order before match order', () => {
    const events = [{ key: '2024b' }, { key: '2024a' }] as Event[];
    const matches = [
      makeMatch({ key: '2024a_qm2', match_number: 2 }),
      makeMatch({ key: '2024b_qm1' }),
      makeMatch({ key: '2024a_qm1' }),
    ];

    const keys = sortMultipleEventsMatches(matches, events).map((m) => m.key);

    expect(keys).toEqual(['2024b_qm1', '2024a_qm1', '2024a_qm2']);
  });
});

describe('matchTitleShort', () => {
  test.each([
    {
      name: 'qualification',
      match: { comp_level: CompLevel.QM, set_number: 1, match_number: 12 },
      playoffType: null,
      expected: 'Quals 12',
    },
    {
      name: 'finals',
      match: { comp_level: CompLevel.F, set_number: 1, match_number: 2 },
      playoffType: PlayoffType.DOUBLE_ELIM_8_TEAM,
      expected: 'Finals 2',
    },
    {
      name: '8 alliance double elim',
      match: { comp_level: CompLevel.SF, set_number: 5, match_number: 1 },
      playoffType: PlayoffType.DOUBLE_ELIM_8_TEAM,
      expected: 'Match 5',
    },
    {
      name: '4 alliance double elim',
      match: { comp_level: CompLevel.SF, set_number: 3, match_number: 1 },
      playoffType: PlayoffType.DOUBLE_ELIM_4_TEAM,
      expected: 'Match 3',
    },
    {
      name: '2015 average score',
      match: { comp_level: CompLevel.QF, set_number: 2, match_number: 3 },
      playoffType: PlayoffType.AVG_SCORE_8_TEAM,
      expected: 'Quarters 3',
    },
    {
      name: 'legacy single elim without a playoff type',
      match: { comp_level: CompLevel.SF, set_number: 2, match_number: 1 },
      playoffType: null,
      expected: 'Semis 2 Match 1',
    },
    {
      name: 'single elim bracket',
      match: { comp_level: CompLevel.QF, set_number: 4, match_number: 2 },
      playoffType: PlayoffType.BRACKET_8_TEAM,
      expected: 'Quarters 4 Match 2',
    },
  ])('$name reads "$expected"', ({ match, playoffType, expected }) => {
    expect(matchTitleShort(match, playoffType)).toBe(expected);
  });
});

describe('matchHasBeenPlayed', () => {
  test('is true once both alliances have a score', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: { red: alliance(10, []), blue: alliance(0, []) },
    });

    expect(matchHasBeenPlayed(match)).toBe(true);
  });

  test('is false while either alliance is unscored', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: { red: alliance(10, []), blue: alliance(-1, []) },
    });

    expect(matchHasBeenPlayed(match)).toBe(false);
  });
});

describe('getTeamMatchResults', () => {
  const matches = [
    makeMatch({
      key: '2024test_qm1',
      alliances: {
        red: alliance(50, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
      winning_alliance: AllianceColor.RED,
    }),
    makeMatch({
      key: '2024test_qm2',
      match_number: 2,
      alliances: {
        red: alliance(10, ['frc254']),
        blue: alliance(50, ['frc1']),
      },
      winning_alliance: AllianceColor.BLUE,
    }),
    makeMatch({
      key: '2024test_qm3',
      match_number: 3,
      alliances: {
        red: alliance(30, ['frc254']),
        blue: alliance(30, ['frc1']),
      },
    }),
    makeMatch({
      key: '2024test_qm4',
      match_number: 4,
      alliances: { red: alliance(50, ['frc1']), blue: alliance(10, ['frc2']) },
      winning_alliance: AllianceColor.RED,
    }),
    makeMatch({
      key: '2024test_sf1m1',
      comp_level: CompLevel.SF,
      alliances: {
        red: alliance(10, ['frc1']),
        blue: alliance(50, ['frc254']),
      },
      winning_alliance: AllianceColor.BLUE,
    }),
    makeMatch({
      key: '2024test_f1m1',
      comp_level: CompLevel.F,
      alliances: {
        red: alliance(60, ['frc1']),
        blue: alliance(50, ['frc254']),
      },
      winning_alliance: AllianceColor.RED,
    }),
    makeMatch({
      key: '2024test_f1m2',
      comp_level: CompLevel.F,
      match_number: 2,
      alliances: {
        red: alliance(-1, ['frc1']),
        blue: alliance(-1, ['frc254']),
      },
    }),
  ];

  function keysOf(results: { wins: Match[]; losses: Match[]; ties: Match[] }) {
    return {
      wins: results.wins.map((m) => m.key),
      losses: results.losses.map((m) => m.key),
      ties: results.ties.map((m) => m.key),
    };
  }

  test('splits the qualification matches the team played into wins, losses and ties', () => {
    const { quals } = getTeamMatchResults('frc254', matches);

    expect(keysOf(quals)).toEqual({
      wins: ['2024test_qm1'],
      losses: ['2024test_qm2'],
      ties: ['2024test_qm3'],
    });
  });

  test('splits the playoff matches the team played, ignoring unplayed ones', () => {
    const { playoff } = getTeamMatchResults('frc254', matches);

    expect(keysOf(playoff)).toEqual({
      wins: ['2024test_sf1m1'],
      losses: ['2024test_f1m1'],
      ties: [],
    });
  });

  test('counts wins and losses into a record', () => {
    expect(calculateTeamRecordsFromMatches('frc254', matches)).toEqual({
      quals: { wins: 1, losses: 1, ties: 1 },
      playoff: { wins: 1, losses: 1, ties: 0 },
    });
  });
});

describe('getTeamsUnpenalizedHighScore', () => {
  test('is undefined without any matches', () => {
    expect(getTeamsUnpenalizedHighScore('frc254', [])).toBeUndefined();
  });

  test('is undefined when the team played none of the matches', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: { red: alliance(50, ['frc1']), blue: alliance(10, ['frc2']) },
    });

    expect(getTeamsUnpenalizedHighScore('frc254', [match])).toBeUndefined();
  });

  test('subtracts camelCase foul points before picking the high score', () => {
    const penalized = makeMatch({
      key: '2024test_qm1',
      alliances: {
        red: alliance(100, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
      score_breakdown: breakdown({ foulPoints: 40 }, { foulPoints: 0 }),
    });
    const clean = makeMatch({
      key: '2024test_qm2',
      match_number: 2,
      alliances: {
        red: alliance(80, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
      score_breakdown: breakdown({ foulPoints: 0 }, { foulPoints: 0 }),
    });

    const high = getTeamsUnpenalizedHighScore('frc254', [penalized, clean]);

    expect(high?.match.key).toBe('2024test_qm2');
    expect(high?.score).toBe(80);
  });

  test('subtracts 2015 snake_case foul points', () => {
    const match = makeMatch({
      key: '2015test_qm1',
      alliances: {
        red: alliance(100, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
      score_breakdown: breakdown({ foul_points: 12 }, { foul_points: 0 }),
    });

    expect(getTeamsUnpenalizedHighScore('frc254', [match])?.score).toBe(88);
  });

  test('uses the raw score without a score breakdown', () => {
    const match = makeMatch({
      key: '2010test_qm1',
      alliances: {
        red: alliance(100, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
    });

    expect(getTeamsUnpenalizedHighScore('frc254', [match])?.score).toBe(100);
  });

  test('uses the raw score when the breakdown has no foul fields', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: {
        red: alliance(100, ['frc254']),
        blue: alliance(10, ['frc1']),
      },
      score_breakdown: breakdown({ totalPoints: 100 }, { totalPoints: 10 }),
    });

    expect(getTeamsUnpenalizedHighScore('frc254', [match])?.score).toBe(100);
  });

  test('scores the blue alliance when the team played blue', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: {
        red: alliance(100, ['frc1']),
        blue: alliance(60, ['frc254']),
      },
      score_breakdown: breakdown({ foulPoints: 0 }, { foulPoints: 5 }),
    });

    const high = getTeamsUnpenalizedHighScore('frc254', [match]);

    expect(high?.score).toBe(55);
    expect(high?.alliance).toBe(match.alliances.blue);
  });
});

describe('getMatchScoreWithoutAdjustPoints', () => {
  test('subtracts camelCase adjust points', () => {
    const match = makeMatch({
      key: '2024test_qm1',
      alliances: { red: alliance(100, []), blue: alliance(50, []) },
      score_breakdown: breakdown({ adjustPoints: 10 }, { adjustPoints: 5 }),
    });

    expect(getMatchScoreWithoutAdjustPoints(match)).toEqual({
      redScore: 90,
      blueScore: 45,
    });
  });

  test('subtracts 2015 snake_case adjust points', () => {
    const match = makeMatch({
      key: '2015test_qm1',
      alliances: { red: alliance(100, []), blue: alliance(50, []) },
      score_breakdown: breakdown({ adjust_points: 10 }, { adjust_points: 5 }),
    });

    expect(getMatchScoreWithoutAdjustPoints(match)).toEqual({
      redScore: 90,
      blueScore: 45,
    });
  });

  test('returns the raw scores without adjust points in the breakdown', () => {
    const match = makeMatch({
      key: '2010test_qm1',
      alliances: { red: alliance(100, []), blue: alliance(50, []) },
    });

    expect(getMatchScoreWithoutAdjustPoints(match)).toEqual({
      redScore: 100,
      blueScore: 50,
    });
  });
});

describe('formatMatchTime', () => {
  // 2026-03-07 is a Saturday; New York is on EST (UTC-5) until March 8.
  const utc = (iso: string) => Date.parse(iso) / 1000;
  const newYork = { timeZone: 'America/New_York' };

  test.each([
    ['2026-03-07T14:30:00Z', 'Sat 9:30 AM'],
    ['2026-03-07T19:05:00Z', 'Sat 2:05 PM'],
    ['2026-03-07T05:00:00Z', 'Sat 12:00 AM'],
  ])('formats %s in the given time zone as %s', (iso, expected) => {
    expect(formatMatchTime(utc(iso), newYork)).toBe(expected);
  });

  test('omits the weekday when asked', () => {
    expect(
      formatMatchTime(utc('2026-03-07T14:30:00Z'), {
        ...newYork,
        weekday: false,
      }),
    ).toBe('9:30 AM');
  });

  test("defaults to the viewer's time zone", () => {
    const nineThirty = new Date(2026, 2, 7, 9, 30).getTime() / 1000;
    expect(formatMatchTime(nineThirty)).toBe('Sat 9:30 AM');
  });
});
