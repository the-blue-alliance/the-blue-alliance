import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  EndgameRobot2022,
  type Match,
  type MatchScoreBreakdown2022,
  type MatchScoreBreakdown2022Alliance,
  TaxiRobot2022,
} from '~/api/tba/read';
import ScoreBreakdown2022 from '~/components/tba/match/scoreBreakdown2022';

// The icon-only helpers are swapped for text so each robot's condition is
// visible in the rendered row. The real helpers are covered in common.test.tsx.
vi.mock('~/components/tba/match/common', async (importOriginal) => ({
  ...(await importOriginal<typeof import('~/components/tba/match/common')>()),
  ConditionalCheckmark: ({
    condition,
    teamKey,
  }: {
    condition: boolean;
    teamKey: string;
  }) => (
    <div>
      {teamKey}={condition ? 'yes' : 'no'}
    </div>
  ),
  ConditionalRpAchieved: ({ condition }: { condition: boolean }) => (
    <div>{condition ? 'achieved' : 'missed'}</div>
  ),
}));

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2022Alliance> = {},
): MatchScoreBreakdown2022Alliance {
  return {
    taxiRobot1: TaxiRobot2022.YES,
    taxiRobot2: TaxiRobot2022.YES,
    taxiRobot3: TaxiRobot2022.NO,
    endgameRobot1: EndgameRobot2022.TRAVERSAL,
    endgameRobot2: EndgameRobot2022.HIGH,
    endgameRobot3: EndgameRobot2022.MID,
    autoCargoLowerNear: 1,
    autoCargoUpperNear: 3,
    autoTaxiPoints: 4,
    autoCargoPoints: 14,
    autoPoints: 18,
    teleopCargoLowerNear: 5,
    teleopCargoUpperNear: 12,
    teleopCargoPoints: 29,
    endgamePoints: 31,
    teleopPoints: 60,
    quintetAchieved: true,
    cargoBonusRankingPoint: true,
    hangarBonusRankingPoint: false,
    foulCount: 2,
    techFoulCount: 1,
    foulPoints: 16,
    adjustPoints: 0,
    rp: 4,
    totalPoints: 94,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2022Alliance> = {},
  blue: Partial<MatchScoreBreakdown2022Alliance> = {},
): MatchScoreBreakdown2022 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance({
      taxiRobot1: TaxiRobot2022.NO,
      taxiRobot2: TaxiRobot2022.NO,
      taxiRobot3: TaxiRobot2022.YES,
      endgameRobot1: EndgameRobot2022.LOW,
      endgameRobot2: EndgameRobot2022.NONE,
      endgameRobot3: undefined,
      autoCargoLowerNear: 0,
      autoCargoUpperNear: 2,
      autoTaxiPoints: 2,
      autoCargoPoints: 8,
      autoPoints: 10,
      teleopCargoLowerNear: 3,
      teleopCargoUpperNear: 7,
      teleopCargoPoints: 17,
      endgamePoints: 4,
      teleopPoints: 21,
      quintetAchieved: false,
      cargoBonusRankingPoint: false,
      hangarBonusRankingPoint: true,
      foulCount: 3,
      techFoulCount: 0,
      foulPoints: 12,
      adjustPoints: -5,
      rp: 1,
      totalPoints: 43,
      ...blue,
    }),
  };
}

const match: Match = {
  key: '2022test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 94,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 43,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2022test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function renderBreakdown(scoreBreakdown = makeBreakdown()) {
  return render(
    <ScoreBreakdown2022 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreBreakdown2022', () => {
  test('shows each robot taxi result with alliance taxi points', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: 'frc254=yes frc1114=yes frc2056=no (+4) Taxi frc148=no frc217=no frc33=yes (+2)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Auto Cargo Lower Hub', red: '1', blue: '0' },
    { label: 'Auto Cargo Upper Hub', red: '3', blue: '2' },
    { label: 'Auto Cargo Points', red: '14', blue: '8' },
    { label: 'Total Auto', red: '18', blue: '10' },
    { label: 'Teleop Cargo Lower Hub', red: '5', blue: '3' },
    { label: 'Teleop Cargo Upper Hub', red: '12', blue: '7' },
    { label: 'Teleop Cargo Points', red: '29', blue: '17' },
    { label: 'Endgame Points', red: '31', blue: '4' },
    { label: 'Total Teleop', red: '60', blue: '21' },
    { label: 'Adjustments', red: '0', blue: '-5' },
    { label: 'Total Score', red: '94', blue: '43' },
    { label: 'RP', red: '+4 RP', blue: '+1 RP' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('shows zero cargo counts when the near-hub counts are missing', () => {
    renderBreakdown(
      makeBreakdown(
        {
          autoCargoLowerNear: undefined,
          autoCargoUpperNear: undefined,
          teleopCargoLowerNear: undefined,
          teleopCargoUpperNear: undefined,
        },
        {
          autoCargoLowerNear: undefined,
          autoCargoUpperNear: undefined,
          teleopCargoLowerNear: undefined,
          teleopCargoUpperNear: undefined,
        },
      ),
    );

    expect(
      screen.getAllByRole('row', { name: /^0 (Auto|Teleop) Cargo \w+ Hub 0$/ }),
    ).toHaveLength(4);
  });

  test.each([
    { name: '254 Traversal (+15) Robot 1 Endgame 148 Low (+4)' },
    { name: '1114 High (+10) Robot 2 Endgame 217 None (+0)' },
    { name: '2056 Mid (+6) Robot 3 Endgame 33 None (+0)' },
  ])('shows the climb level and points in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test('shows an unknown endgame level as None with zero points', () => {
    renderBreakdown(
      makeBreakdown({
        endgameRobot1: 'Hover' as EndgameRobot2022,
      }),
    );

    expect(
      screen.getByRole('row', {
        name: '254 Hover (+0) Robot 1 Endgame 148 Low (+4)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Quintet Achieved', red: 'achieved', blue: 'missed' },
    { label: 'Cargo Bonus RP', red: 'achieved', blue: 'missed' },
    { label: 'Hangar Bonus RP', red: 'missed', blue: 'achieved' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('treats missing bonus flags as not achieved', () => {
    renderBreakdown(
      makeBreakdown(
        {
          quintetAchieved: undefined,
          cargoBonusRankingPoint: undefined,
          hangarBonusRankingPoint: undefined,
        },
        {
          quintetAchieved: undefined,
          cargoBonusRankingPoint: undefined,
          hangarBonusRankingPoint: undefined,
        },
      ),
    );

    expect(
      screen.getAllByRole('row', { name: /^missed .* missed$/ }),
    ).toHaveLength(3);
  });

  test('credits each alliance with the fouls the other alliance committed', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: /^Regular: ?3 \(\+12\) Tech: ?0 \(\+0\) Fouls Regular: ?2 \(\+8\) Tech: ?1 \(\+8\)$/,
      }),
    ).toBeTruthy();
  });

  test('shows an empty RP value when the ranking points are null', () => {
    renderBreakdown(makeBreakdown({ rp: null }, { rp: null }));

    expect(screen.getByRole('row', { name: '+ RP RP + RP' })).toBeTruthy();
  });
});
