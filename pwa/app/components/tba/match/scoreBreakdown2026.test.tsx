import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type HubScore2026,
  type Match,
  type MatchScoreBreakdown2026,
  type MatchScoreBreakdown2026Alliance,
  TowerRobot2026,
} from '~/api/tba/read';
import ScoreBreakdown2026 from '~/components/tba/match/scoreBreakdown2026';

// The icon-only helpers are swapped for text so each robot's condition is
// visible in the rendered row. The real helpers are covered in common.test.tsx.
vi.mock('~/components/tba/match/common', async (importOriginal) => ({
  ...(await importOriginal<typeof import('~/components/tba/match/common')>()),
  ConditionalBadge: ({
    condition,
    teamKey,
    alignIcon,
  }: {
    condition: boolean;
    teamKey: string;
    alignIcon: 'left' | 'right';
  }) => (
    <div>
      {teamKey}={condition ? 'yes' : 'no'}:{alignIcon}
    </div>
  ),
  ConditionalRpAchieved: ({ condition }: { condition: boolean }) => (
    <div>{condition ? 'achieved' : 'missed'}</div>
  ),
}));

function makeHubScore(overrides: Partial<HubScore2026> = {}): HubScore2026 {
  return {
    autoCount: 12,
    autoPoints: 12,
    transitionCount: 4,
    transitionPoints: 4,
    shift1Count: 10,
    shift1Points: 10,
    shift2Count: 20,
    shift2Points: 20,
    shift3Count: 15,
    shift3Points: 15,
    shift4Count: 5,
    shift4Points: 5,
    endgameCount: 7,
    endgamePoints: 7,
    teleopCount: 61,
    teleopPoints: 61,
    totalCount: 73,
    totalPoints: 73,
    ...overrides,
  };
}

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2026Alliance> = {},
): MatchScoreBreakdown2026Alliance {
  return {
    autoTowerRobot1: TowerRobot2026.LEVEL1,
    autoTowerRobot2: TowerRobot2026.NONE,
    autoTowerRobot3: TowerRobot2026.NONE,
    autoTowerPoints: 6,
    totalAutoPoints: 18,
    hubScore: makeHubScore(),
    endGameTowerRobot1: TowerRobot2026.LEVEL3,
    endGameTowerRobot2: TowerRobot2026.LEVEL2,
    endGameTowerRobot3: TowerRobot2026.LEVEL1,
    endGameTowerPoints: 31,
    totalTowerPoints: 37,
    totalTeleopPoints: 92,
    energizedAchieved: true,
    superchargedAchieved: true,
    traversalAchieved: false,
    minorFoulCount: 1,
    majorFoulCount: 2,
    foulPoints: 10,
    g206Penalty: false,
    adjustPoints: 0,
    totalPoints: 119,
    rp: 5,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2026Alliance> = {},
  blue: Partial<MatchScoreBreakdown2026Alliance> = {},
): MatchScoreBreakdown2026 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance({
      autoTowerRobot1: TowerRobot2026.NONE,
      autoTowerRobot2: TowerRobot2026.NONE,
      autoTowerRobot3: TowerRobot2026.LEVEL2,
      autoTowerPoints: 10,
      totalAutoPoints: 14,
      hubScore: makeHubScore({
        autoCount: 4,
        autoPoints: 4,
        transitionCount: 2,
        transitionPoints: 2,
        shift1Count: 8,
        shift1Points: 8,
        shift2Count: 6,
        shift2Points: 6,
        shift3Count: 4,
        shift3Points: 4,
        shift4Count: 2,
        shift4Points: 2,
        endgameCount: 3,
        endgamePoints: 3,
        teleopCount: 25,
        teleopPoints: 25,
        totalCount: 29,
        totalPoints: 29,
      }),
      endGameTowerRobot1: TowerRobot2026.LEVEL1,
      endGameTowerRobot2: TowerRobot2026.NONE,
      endGameTowerRobot3: TowerRobot2026.NONE,
      endGameTowerPoints: 6,
      totalTowerPoints: 16,
      totalTeleopPoints: 31,
      energizedAchieved: false,
      superchargedAchieved: false,
      traversalAchieved: true,
      minorFoulCount: 2,
      majorFoulCount: 0,
      foulPoints: 35,
      adjustPoints: 0,
      totalPoints: 49,
      rp: 1,
      ...blue,
    }),
  };
}

const match: Match = {
  key: '2026test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 119,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 49,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2026test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function renderBreakdown(scoreBreakdown = makeBreakdown()) {
  return render(
    <ScoreBreakdown2026 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreBreakdown2026', () => {
  test('shows which robots climbed the tower in auto with the auto tower points', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: 'frc254=yes:left frc1114=no:left frc2056=no:left 6 Auto Tower 10 frc148=no:right frc217=no:right frc33=yes:right',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Total Auto', red: '18', blue: '14' },
    { label: 'Transition Fuel', red: '4', blue: '2' },
    { label: 'Shift 1 Count', red: '10', blue: '8' },
    { label: 'Shift 2 Count', red: '20', blue: '6' },
    { label: 'Shift 3 Count', red: '15', blue: '4' },
    { label: 'Shift 4 Count', red: '5', blue: '2' },
    {
      label: 'Shift Points (1/2/3/4)',
      red: '10 / 20 / 15 / 5',
      blue: '8 / 6 / 4 / 2',
    },
    { label: 'Endgame Hub Fuel', red: '7', blue: '3' },
    { label: 'Teleop Count', red: '61', blue: '25' },
    { label: 'Teleop Hub Points', red: '61', blue: '25' },
    { label: 'Endgame Tower Points', red: '31', blue: '6' },
    { label: 'Total Tower Points', red: '37', blue: '16' },
    { label: 'Total Teleop', red: '92', blue: '31' },
    // Fouls from 2026cmptx_sf8m1; each alliance's foulPoints come from the other's fouls.
    { label: 'Fouls / Major Fouls Committed', red: '1 / 2', blue: '2 / 0' },
    { label: 'Foul Points Received', red: '10', blue: '35' },
    { label: 'Total Score', red: '119', blue: '49' },
    { label: 'RP', red: '+5 RP', blue: '+1 RP' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test.each([
    { name: '254 Level 3 (+15) Robot 1 Endgame 148 Level 1 (+6)' },
    { name: '1114 Level 2 (+10) Robot 2 Endgame 217 None (+0)' },
    { name: '2056 Level 1 (+6) Robot 3 Endgame 33 None (+0)' },
  ])('shows the tower level and points in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test.each([
    { label: 'Energized Bonus', red: 'achieved', blue: 'missed' },
    { label: 'Supercharged Bonus', red: 'achieved', blue: 'missed' },
    { label: 'Traversal Bonus', red: 'missed', blue: 'achieved' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('hides the adjustments row when neither alliance was adjusted', () => {
    renderBreakdown();

    expect(screen.queryByText('Adjustments')).toBeNull();
  });

  test('shows the adjustments row when the red alliance was adjusted', () => {
    renderBreakdown(makeBreakdown({ adjustPoints: -10 }));

    expect(screen.getByRole('row', { name: '-10 Adjustments 0' })).toBeTruthy();
  });

  test('shows the adjustments row when the blue alliance was adjusted', () => {
    renderBreakdown(makeBreakdown({}, { adjustPoints: 5 }));

    expect(screen.getByRole('row', { name: '0 Adjustments 5' })).toBeTruthy();
  });

  test('hides the adjustments row when adjustments are missing', () => {
    renderBreakdown(
      makeBreakdown(
        { adjustPoints: undefined as unknown as number },
        { adjustPoints: undefined as unknown as number },
      ),
    );

    expect(screen.queryByText('Adjustments')).toBeNull();
  });
});
