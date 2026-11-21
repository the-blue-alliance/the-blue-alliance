import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  EndgameRobot2022,
  type MatchScoreBreakdown2022,
  type MatchScoreBreakdown2022Alliance,
  TaxiRobot2022,
} from '~/api/tba/read';
import ScoreBreakdown2022 from '~/components/tba/match/scoreBreakdown2022';
import { makeMatch } from '~/test/factories';

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

const match = makeMatch({
  key: '2022test_qm1',
  event_key: '2022test',
});

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
        name: 'frc254=yes frc1114=yes frc2056=no (+4) Red leads Taxi frc148=no frc217=no frc33=yes (+2)',
      }),
    ).toBeTruthy();
  });

  test.each([
    {
      label: 'Auto Cargo Lower Hub',
      name: '1 Red leads Auto Cargo Lower Hub 0',
    },
    {
      label: 'Auto Cargo Upper Hub',
      name: '3 Red leads Auto Cargo Upper Hub 2',
    },
    { label: 'Auto Cargo Points', name: '14 Red leads Auto Cargo Points 8' },
    { label: 'Total Auto', name: '18 Red leads Total Auto 10' },
    {
      label: 'Teleop Cargo Lower Hub',
      name: '5 Red leads Teleop Cargo Lower Hub 3',
    },
    {
      label: 'Teleop Cargo Upper Hub',
      name: '12 Red leads Teleop Cargo Upper Hub 7',
    },
    {
      label: 'Teleop Cargo Points',
      name: '29 Red leads Teleop Cargo Points 17',
    },
    { label: 'Endgame Points', name: '31 Red leads Endgame Points 4' },
    { label: 'Total Teleop', name: '60 Red leads Total Teleop 21' },
    { label: 'Adjustments', name: '0 Red leads Adjustments -5' },
    { label: 'Total Score', name: '94 Red leads Total Score 43' },
    { label: 'RP', name: '+4 RP Red leads RP +1 RP' },
  ])('shows $label for both alliances', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
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

  // Counts and foul points from 2022gal_qm73; each alliance's foulPoints come from the other's fouls.
  test('shows the fouls each alliance committed and the foul points it received', () => {
    renderBreakdown(
      makeBreakdown(
        { foulCount: 5, techFoulCount: 1, foulPoints: 4 },
        { foulCount: 1, techFoulCount: 0, foulPoints: 28 },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: '5 / 1 Fouls / Tech Fouls Committed 1 / 0',
      }),
    ).toBeTruthy();
    expect(
      screen.getByRole('row', { name: '4 Foul Points Received Blue leads 28' }),
    ).toBeTruthy();
  });

  test('shows an empty RP value when the ranking points are null', () => {
    renderBreakdown(makeBreakdown({ rp: null }, { rp: null }));

    expect(screen.getByRole('row', { name: '+ RP RP + RP' })).toBeTruthy();
  });
});
