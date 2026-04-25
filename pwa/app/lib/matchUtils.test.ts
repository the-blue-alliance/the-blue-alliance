import { describe, expect, test } from 'vitest';

import type { Match } from '~/api/tba/read';
import { AllianceColor, CompLevel } from '~/api/tba/read';
import { getAllianceMatchResult, isValidMatchKey } from '~/lib/matchUtils';

describe.concurrent('isValidMatchKey', () => {
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

describe.concurrent('getAllianceMatchResult', () => {
  // Helper function to create a mock match
  function createMockMatch(
    key: string,
    redScore: number,
    blueScore: number,
    winningAlliance: '' | AllianceColor,
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
    const match = createMockMatch('2024test_qm1', -1, -1, '');
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
    const match = createMockMatch('2024test_qm1', 100, 100, '');
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'tie',
    );
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'tie',
    );
  });

  test('returns tie for 2015 match with official strategy', () => {
    const match = createMockMatch('2015test_qm1', 100, 80, '');
    expect(getAllianceMatchResult(match, AllianceColor.RED, 'official')).toBe(
      'tie',
    );
    expect(getAllianceMatchResult(match, AllianceColor.BLUE, 'official')).toBe(
      'tie',
    );
  });

  test('returns win/loss for 2015 match with score-based strategy when red scores higher', () => {
    const match = createMockMatch('2015test_qm1', 100, 80, '');
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('win');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('loss');
  });

  test('returns win/loss for 2015 match with score-based strategy when blue scores higher', () => {
    const match = createMockMatch('2015test_qm1', 80, 100, '');
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('loss');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('win');
  });

  test('returns tie for 2015 match with score-based strategy when scores are equal', () => {
    const match = createMockMatch('2015test_qm1', 100, 100, '');
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
    const match = createMockMatch('2015test_sf1m1', 100, 80, '');
    match.comp_level = CompLevel.SF;
    expect(
      getAllianceMatchResult(match, AllianceColor.RED, 'score-based'),
    ).toBe('win');
    expect(
      getAllianceMatchResult(match, AllianceColor.BLUE, 'score-based'),
    ).toBe('loss');
  });
});
