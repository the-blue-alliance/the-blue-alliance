import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  AutoLineRobot2024,
  CompLevel,
  EndGameRobot2025,
  type Match,
  type MatchScoreBreakdown2025,
  type MatchScoreBreakdown2025Alliance,
  type ReefRow2025,
} from '~/api/tba/read';
import ScoreBreakdown2025 from '~/components/tba/match/scoreBreakdown2025';

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

const emptyReefRow: ReefRow2025 = {
  nodeA: false,
  nodeB: false,
  nodeC: false,
  nodeD: false,
  nodeE: false,
  nodeF: false,
  nodeG: false,
  nodeH: false,
  nodeI: false,
  nodeJ: false,
  nodeK: false,
  nodeL: false,
};

function makeReef(
  top: number,
  mid: number,
  bot: number,
  trough: number,
): MatchScoreBreakdown2025Alliance['autoReef'] {
  return {
    topRow: emptyReefRow,
    midRow: emptyReefRow,
    botRow: emptyReefRow,
    trough,
    tba_topRowCount: top,
    tba_midRowCount: mid,
    tba_botRowCount: bot,
  };
}

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2025Alliance> = {},
): MatchScoreBreakdown2025Alliance {
  return {
    autoLineRobot1: AutoLineRobot2024.YES,
    autoLineRobot2: AutoLineRobot2024.YES,
    autoLineRobot3: AutoLineRobot2024.NO,
    autoMobilityPoints: 6,
    autoReef: makeReef(2, 1, 0, 3),
    autoCoralCount: 6,
    autoCoralPoints: 26,
    autoPoints: 32,
    teleopReef: makeReef(8, 5, 4, 2),
    teleopCoralCount: 19,
    teleopCoralPoints: 71,
    wallAlgaeCount: 3,
    netAlgaeCount: 4,
    algaePoints: 34,
    endGameRobot1: EndGameRobot2025.DEEP_CAGE,
    endGameRobot2: EndGameRobot2025.SHALLOW_CAGE,
    endGameRobot3: EndGameRobot2025.PARKED,
    endGameBargePoints: 20,
    teleopPoints: 125,
    coopertitionCriteriaMet: true,
    autoBonusAchieved: true,
    coralBonusAchieved: true,
    bargeBonusAchieved: false,
    foulCount: 3,
    techFoulCount: 1,
    foulPoints: 12,
    g206Penalty: false,
    g410Penalty: false,
    g418Penalty: false,
    g428Penalty: false,
    adjustPoints: 0,
    rp: 5,
    totalPoints: 169,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2025Alliance> = {},
  blue: Partial<MatchScoreBreakdown2025Alliance> = {},
): MatchScoreBreakdown2025 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance({
      autoLineRobot1: AutoLineRobot2024.NO,
      autoLineRobot2: AutoLineRobot2024.NO,
      autoLineRobot3: AutoLineRobot2024.YES,
      autoMobilityPoints: 3,
      autoReef: makeReef(1, 0, 0, 1),
      autoCoralCount: 2,
      autoCoralPoints: 10,
      autoPoints: 13,
      teleopReef: makeReef(3, 2, 6, 5),
      teleopCoralCount: 16,
      teleopCoralPoints: 44,
      wallAlgaeCount: 1,
      netAlgaeCount: 0,
      algaePoints: 6,
      endGameRobot1: EndGameRobot2025.NONE,
      endGameRobot2: EndGameRobot2025.PARKED,
      endGameRobot3: EndGameRobot2025.NONE,
      endGameBargePoints: 2,
      teleopPoints: 52,
      coopertitionCriteriaMet: false,
      autoBonusAchieved: false,
      coralBonusAchieved: false,
      bargeBonusAchieved: true,
      foulCount: 2,
      techFoulCount: 0,
      foulPoints: 6,
      adjustPoints: -4,
      rp: 1,
      totalPoints: 67,
      ...blue,
    }),
  };
}

const match: Match = {
  key: '2025test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 169,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 67,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2025test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function renderBreakdown(scoreBreakdown = makeBreakdown()) {
  return render(
    <ScoreBreakdown2025 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreBreakdown2025', () => {
  test('shows each robot auto leave result with alliance mobility points', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: 'frc254=yes frc1114=yes frc2056=no (+6) Auto Leave frc148=no frc217=no frc33=yes (+3)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { name: 'L4 2 Auto Coral Count 1 L4' },
    { name: 'L3 1 0 L3' },
    { name: 'L2 0 0 L2' },
    { name: 'L1 3 1 L1' },
  ])('shows the auto coral level count in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test.each([
    { name: 'L4 8 Teleop Coral Count 3 L4' },
    { name: 'L3 5 2 L3' },
    { name: 'L2 4 6 L2' },
    { name: 'L1 2 5 L1' },
  ])('shows the teleop coral level count in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test.each([
    { label: 'Auto Coral Points', red: '26', blue: '10' },
    { label: 'Total Auto', red: '32', blue: '13' },
    { label: 'Teleop Coral Points', red: '71', blue: '44' },
    { label: 'Processor Algae Count', red: '3', blue: '1' },
    { label: 'Net Algae Count', red: '4', blue: '0' },
    { label: 'Algae Points', red: '34', blue: '6' },
    { label: 'Barge Points', red: '20', blue: '2' },
    { label: 'Total Teleop', red: '125', blue: '52' },
    { label: 'Fouls / Major Fouls', red: '3 / 1', blue: '2 / 0' },
    { label: 'Foul Points', red: '12', blue: '6' },
    { label: 'Adjustments', red: '0', blue: '-4' },
    { label: 'Total Score', red: '169', blue: '67' },
    { label: 'RP', red: '+5 RP', blue: '+1 RP' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test.each([
    { name: '254 Deep Cage (+12) Robot 1 Endgame 148 None (+0)' },
    { name: '1114 Shallow Cage (+6) Robot 2 Endgame 217 Parked (+2)' },
    { name: '2056 Parked (+2) Robot 3 Endgame 33 None (+0)' },
  ])('shows the cage state and points in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test('shows a missing endgame state as None with zero points', () => {
    renderBreakdown(
      makeBreakdown({
        endGameRobot1: undefined as unknown as EndGameRobot2025,
      }),
    );

    expect(
      screen.getByRole('row', {
        name: '254 None (+0) Robot 1 Endgame 148 None (+0)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Coopertition Criteria Met', red: 'achieved', blue: 'missed' },
    { label: 'Auto Bonus', red: 'achieved', blue: 'missed' },
    { label: 'Coral Bonus', red: 'achieved', blue: 'missed' },
    { label: 'Barge Bonus', red: 'missed', blue: 'achieved' },
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
          coopertitionCriteriaMet: undefined,
          autoBonusAchieved: undefined,
          coralBonusAchieved: undefined,
          bargeBonusAchieved: undefined,
        },
        {
          coopertitionCriteriaMet: undefined,
          autoBonusAchieved: undefined,
          coralBonusAchieved: undefined,
          bargeBonusAchieved: undefined,
        },
      ),
    );

    expect(
      screen.getAllByRole('row', { name: /^missed .* missed$/ }),
    ).toHaveLength(4);
  });
});
