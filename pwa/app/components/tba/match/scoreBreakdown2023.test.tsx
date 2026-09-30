import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  AutoChargeStationRobot2023,
  CompLevel,
  EndGameChargeStationRobot2023,
  type Match,
  type MatchScoreBreakdown2023,
  type MatchScoreBreakdown2023Alliance,
  MobilityRobot2023,
} from '~/api/tba/read';
import ScoreBreakdown2023 from '~/components/tba/match/scoreBreakdown2023';

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
    // Normalised so these rows don't depend on whether the component passes
    // "frc254" or "254"; which one it should pass is Bug #58, covered by
    // its own failing-test PR.
    <div>
      {teamKey.replace(/^frc/, '')}={condition ? 'yes' : 'no'}
    </div>
  ),
  ConditionalRpAchieved: ({ condition }: { condition: boolean }) => (
    <div>{condition ? 'achieved' : 'missed'}</div>
  ),
}));

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2023Alliance> = {},
): MatchScoreBreakdown2023Alliance {
  return {
    mobilityRobot1: MobilityRobot2023.YES,
    mobilityRobot2: MobilityRobot2023.YES,
    mobilityRobot3: MobilityRobot2023.NO,
    autoMobilityPoints: 6,
    autoGamePieceCount: 3,
    autoGamePiecePoints: 12,
    autoChargeStationRobot1: AutoChargeStationRobot2023.DOCKED,
    autoChargeStationRobot2: AutoChargeStationRobot2023.NONE,
    autoChargeStationRobot3: undefined,
    autoPoints: 20,
    teleopGamePieceCount: 15,
    extraGamePieceCount: 2,
    teleopGamePiecePoints: 55,
    endGameChargeStationRobot1: EndGameChargeStationRobot2023.DOCKED,
    endGameChargeStationRobot2: EndGameChargeStationRobot2023.PARKED,
    endGameChargeStationRobot3: EndGameChargeStationRobot2023.PARK,
    teleopPoints: 78,
    links: [
      { nodes: ['Cone', 'Cube', 'Cone'], row: 'Top' },
      { nodes: ['Cone', 'Cube', 'Cone'], row: 'Mid' },
      { nodes: ['Cube', 'Cube', 'Cube'], row: 'Bottom' },
    ],
    linkPoints: 15,
    coopertitionCriteriaMet: true,
    sustainabilityBonusAchieved: true,
    activationBonusAchieved: false,
    foulCount: 2,
    techFoulCount: 1,
    foulPoints: 22,
    adjustPoints: 0,
    totalPoints: 120,
    rp: 4,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2023Alliance> = {},
  blue: Partial<MatchScoreBreakdown2023Alliance> = {},
): MatchScoreBreakdown2023 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance({
      mobilityRobot1: MobilityRobot2023.NO,
      mobilityRobot2: MobilityRobot2023.NO,
      mobilityRobot3: MobilityRobot2023.YES,
      autoMobilityPoints: 3,
      autoGamePieceCount: 1,
      autoGamePiecePoints: 4,
      autoChargeStationRobot1: AutoChargeStationRobot2023.NONE,
      autoChargeStationRobot2: AutoChargeStationRobot2023.DOCKED,
      autoChargeStationRobot3: AutoChargeStationRobot2023.DOCKED,
      autoPoints: 8,
      teleopGamePieceCount: 9,
      extraGamePieceCount: 0,
      teleopGamePiecePoints: 30,
      endGameChargeStationRobot1: EndGameChargeStationRobot2023.NONE,
      endGameChargeStationRobot2: EndGameChargeStationRobot2023.PARK,
      endGameChargeStationRobot3: undefined,
      teleopPoints: 40,
      links: undefined,
      linkPoints: 0,
      coopertitionCriteriaMet: false,
      sustainabilityBonusAchieved: false,
      activationBonusAchieved: true,
      foulCount: 3,
      techFoulCount: 0,
      foulPoints: 10,
      adjustPoints: -5,
      totalPoints: 53,
      rp: 1,
      ...blue,
    }),
  };
}

const match: Match = {
  key: '2023test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 120,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 53,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2023test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function renderBreakdown(scoreBreakdown = makeBreakdown()) {
  return render(
    <ScoreBreakdown2023 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreBreakdown2023', () => {
  test('shows each robot mobility result', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: '254=yes 1114=yes 2056=no Mobility 148=no 217=no 33=yes',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Auto Game Piece Count', red: '3', blue: '1' },
    { label: 'Auto Game Piece Points', red: '12', blue: '4' },
    { label: 'Total Auto', red: '20', blue: '8' },
    { label: 'Game Piece Count', red: '15', blue: '9' },
    { label: 'Supercharged Node', red: '2', blue: '0' },
    { label: 'Game Piece Points', red: '55', blue: '30' },
    { label: 'Total Teleop', red: '78', blue: '40' },
    { label: 'Adjustments', red: '0', blue: '-5' },
    { label: 'Total Score', red: '120', blue: '53' },
    { label: 'RP', red: '+4 RP', blue: '+1 RP' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('lists only the robots docked on the charge station in auto', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: '254 Charge Station Auto 217 33' }),
    ).toBeTruthy();
  });

  test.each([
    { name: '254 Docked (+10) Robot 1 Endgame 148 None (+0)' },
    { name: '1114 Parked (+2) Robot 2 Endgame 217 Park (+2)' },
    { name: '2056 Park (+2) Robot 3 Endgame 33 (+0)' },
  ])('shows the charge station state and points in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test('shows the link count with link points', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: '3 (+15) Links (+0)' }),
    ).toBeTruthy();
  });

  test('shows no link count when links are null', () => {
    renderBreakdown(makeBreakdown({ links: null, linkPoints: 0 }));

    expect(screen.getByRole('row', { name: '(+0) Links (+0)' })).toBeTruthy();
  });

  test.each([
    { label: 'Coopertition Criteria Met', red: 'achieved', blue: 'missed' },
    { label: 'Sustainability Bonus', red: 'achieved', blue: 'missed' },
    { label: 'Activation Bonus', red: 'missed', blue: 'achieved' },
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
          sustainabilityBonusAchieved: undefined,
          activationBonusAchieved: undefined,
        },
        {
          coopertitionCriteriaMet: undefined,
          sustainabilityBonusAchieved: undefined,
          activationBonusAchieved: undefined,
        },
      ),
    );

    expect(
      screen.getAllByRole('row', { name: /^missed .* missed$/ }),
    ).toHaveLength(3);
  });

  // Both alliances get identical counts here: which alliance's counts belong
  // under which column is Bug #56, covered by its own failing-test PR.
  test('shows foul counts with derived points', () => {
    renderBreakdown(
      makeBreakdown(
        { foulCount: 2, techFoulCount: 1 },
        { foulCount: 2, techFoulCount: 1 },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: /^Regular: ?2 \(\+10\) Tech: ?1 \(\+12\) Fouls \/ Tech Fouls Regular: ?2 \(\+10\) Tech: ?1 \(\+12\)$/,
      }),
    ).toBeTruthy();
  });
});
