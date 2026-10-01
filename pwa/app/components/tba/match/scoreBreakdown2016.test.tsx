import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  Match,
  MatchScoreBreakdown2016,
  MatchScoreBreakdown2016Alliance,
  Position2016,
  RobotAuto2016WithUnknown,
  RobotAuto2016WithoutUnknown,
  TowerFace2016,
} from '~/api/tba/read';
import ScoreBreakdown2016 from '~/components/tba/match/scoreBreakdown2016';

vi.mock('~icons/mdi/check', () => ({
  default: () => <img alt="Achieved" />,
}));

vi.mock('~icons/mdi/close', () => ({
  default: () => <img alt="Not achieved" />,
}));

vi.mock('~icons/mdi/arrow-left', () => ({
  default: () => <img alt="Red leads" />,
}));

vi.mock('~icons/mdi/arrow-right', () => ({
  default: () => <img alt="Blue leads" />,
}));

const match: Match = {
  key: '2016nytr_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 120,
      team_keys: ['frc254', 'frc1678', 'frc971'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 80,
      team_keys: ['frc148', 'frc2056', 'frc118'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2016nytr',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2016Alliance> = {},
): MatchScoreBreakdown2016Alliance {
  return {
    autoPoints: 32,
    teleopPoints: 88,
    breachPoints: 20,
    foulPoints: 10,
    capturePoints: 25,
    adjustPoints: 0,
    totalPoints: 120,
    tba_rpEarned: 3,
    robot1Auto: RobotAuto2016WithUnknown.CROSSED,
    robot2Auto: RobotAuto2016WithoutUnknown.REACHED,
    robot3Auto: RobotAuto2016WithUnknown.NONE,
    autoReachPoints: 2,
    autoCrossingPoints: 10,
    autoBouldersLow: 1,
    autoBouldersHigh: 2,
    autoBoulderPoints: 25,
    teleopCrossingPoints: 40,
    teleopBouldersLow: 4,
    teleopBouldersHigh: 10,
    teleopBoulderPoints: 58,
    teleopDefensesBreached: true,
    teleopChallengePoints: 10,
    teleopScalePoints: 15,
    teleopTowerCaptured: true,
    towerFaceA: TowerFace2016.CHALLENGED,
    towerFaceB: TowerFace2016.SCALED,
    towerFaceC: TowerFace2016.BOTH,
    towerEndStrength: 0,
    techFoulCount: 1,
    foulCount: 2,
    position2: Position2016.A_PORTCULLIS,
    position3: Position2016.B_MOAT,
    position4: Position2016.C_DRAWBRIDGE,
    position5: Position2016.D_ROCK_WALL,
    position1crossings: 3,
    position2crossings: 2,
    position3crossings: 1,
    position4crossings: 0,
    position5crossings: 2,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2016Alliance> = {},
  blue: Partial<MatchScoreBreakdown2016Alliance> = {},
): MatchScoreBreakdown2016 {
  return { red: makeAlliance(red), blue: makeAlliance(blue) };
}

function rowFor(label: string): HTMLElement {
  const row = screen.getByText(label).closest('tr');
  if (!row) {
    throw new Error(`No row labelled ${label}`);
  }
  return row;
}

function redCell(label: string): HTMLElement {
  return within(rowFor(label)).getAllByRole('cell')[0];
}

function blueCell(label: string): HTMLElement {
  return within(rowFor(label)).getAllByRole('cell')[2];
}

describe('ScoreBreakdown2016 auto reach/cross', () => {
  test('checks robots that crossed or reached a defense in auto', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({
          robot1Auto: RobotAuto2016WithUnknown.CROSSED,
          robot2Auto: RobotAuto2016WithoutUnknown.REACHED,
          robot3Auto: RobotAuto2016WithUnknown.REACHED,
        })}
        match={match}
      />,
    );

    expect(
      within(redCell('Auto Reach/Cross')).getAllByRole('img', {
        name: 'Achieved',
      }),
    ).toHaveLength(3);
  });

  test('crosses robots that stayed put or have unknown auto', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          {
            robot1Auto: RobotAuto2016WithUnknown.UNKNOWN,
            robot2Auto: RobotAuto2016WithoutUnknown.NONE,
            robot3Auto: undefined,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Auto Reach/Cross')).getAllByRole('img', {
        name: 'Not achieved',
      }),
    ).toHaveLength(3);
  });

  test('checks a second robot that crossed in auto', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          {
            robot1Auto: RobotAuto2016WithUnknown.NONE,
            robot2Auto: RobotAuto2016WithoutUnknown.CROSSED,
            robot3Auto: RobotAuto2016WithUnknown.CROSSED,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Auto Reach/Cross')).getAllByRole('img', {
        name: 'Achieved',
      }),
    ).toHaveLength(2);
  });
});

describe('ScoreBreakdown2016 point rows', () => {
  test.each([
    { label: 'Auto Reach Points', field: 'autoReachPoints' as const },
    { label: 'Auto Crossing Points', field: 'autoCrossingPoints' as const },
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Teleop Crossing Points', field: 'teleopCrossingPoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Adjustments', field: 'adjustPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('37');
    expect(blueCell(label).textContent).toBe('12');
  });

  test.each([
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Adjustments', field: 'adjustPoints' as const },
  ])('shows 0 for $label when the value is missing', ({ label, field }) => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { [field]: undefined },
          { [field]: undefined },
        )}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('0');
    expect(blueCell(label).textContent).toBe('0');
  });

  test('shows auto boulders by goal with their points', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({
          autoBouldersHigh: 2,
          autoBouldersLow: 1,
          autoBoulderPoints: 25,
        })}
        match={match}
      />,
    );

    expect(redCell('Auto Boulders').textContent).toBe('H: 2 / L: 1 (+25)');
  });

  test('shows zero auto boulders when counts are missing', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          {
            autoBouldersHigh: undefined,
            autoBouldersLow: undefined,
            autoBoulderPoints: 0,
          },
        )}
        match={match}
      />,
    );

    expect(blueCell('Auto Boulders').textContent).toBe('H: 0 / L: 0 (+0)');
  });

  test('shows teleop boulders by goal with their points', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          {
            teleopBouldersHigh: 10,
            teleopBouldersLow: 4,
            teleopBoulderPoints: 58,
          },
        )}
        match={match}
      />,
    );

    expect(blueCell('Teleop Boulders').textContent).toBe('H: 10 / L: 4 (+58)');
  });

  test('sums challenge and scale points into one tower row', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({
          teleopChallengePoints: 10,
          teleopScalePoints: 15,
        })}
        match={match}
      />,
    );

    expect(redCell('Tower Challenge/Scale').textContent).toBe('25');
  });

  test('shows breach and capture points side by side', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { breachPoints: 20, capturePoints: 25 },
          { breachPoints: 0, capturePoints: 25 },
        )}
        match={match}
      />,
    );

    expect(redCell('Breach / Capture Points').textContent).toBe('20 / 25');
    expect(blueCell('Breach / Capture Points').textContent).toBe('0 / 25');
  });
});

describe('ScoreBreakdown2016 defenses', () => {
  test('shows low bar crossings for defense 1', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { position1crossings: 3 },
          { position1crossings: 0 },
        )}
        match={match}
      />,
    );

    expect(redCell('Defense 1 — Low Bar').textContent).toBe('3x Cross');
    expect(blueCell('Defense 1 — Low Bar').textContent).toBe('0x Cross');
  });

  test('shows zero crossings when the count is missing', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({
          position1crossings: undefined as unknown as number,
        })}
        match={match}
      />,
    );

    expect(redCell('Defense 1 — Low Bar').textContent).toBe('0x Cross');
  });

  test.each([
    {
      label: 'Defense 2',
      position: 2 as const,
      value: Position2016.A_PORTCULLIS,
      name: 'Portcullis',
    },
    {
      label: 'Defense 2',
      position: 2 as const,
      value: Position2016.A_CHEVAL_DE_FRISE,
      name: 'Cheval de Frise',
    },
    {
      label: 'Defense 3',
      position: 3 as const,
      value: Position2016.B_MOAT,
      name: 'Moat',
    },
    {
      label: 'Defense 3',
      position: 3 as const,
      value: Position2016.B_RAMPARTS,
      name: 'Ramparts',
    },
    {
      label: 'Defense 4',
      position: 4 as const,
      value: Position2016.C_DRAWBRIDGE,
      name: 'Drawbridge',
    },
    {
      label: 'Defense 4',
      position: 4 as const,
      value: Position2016.C_SALLY_PORT,
      name: 'Sally Port',
    },
    {
      label: 'Defense 5',
      position: 5 as const,
      value: Position2016.D_ROCK_WALL,
      name: 'Rock Wall',
    },
    {
      label: 'Defense 5',
      position: 5 as const,
      value: Position2016.D_ROUGH_TERRAIN,
      name: 'Rough Terrain',
    },
  ])('names $value as $name in $label', ({ label, position, value, name }) => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({
          [`position${position}`]: value,
          [`position${position}crossings`]: 2,
        })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe(`${name} — 2x Cross`);
  });

  test('falls back to the raw value for an unrecognised defense', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          { position3: Position2016.NOT_SPECIFIED, position3crossings: 1 },
        )}
        match={match}
      />,
    );

    expect(blueCell('Defense 3').textContent).toBe('NotSpecified — 1x Cross');
  });

  test('labels an empty defense slot by its position', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          {},
          { position4: Position2016[''], position4crossings: 0 },
        )}
        match={match}
      />,
    );

    expect(blueCell('Defense 4').textContent).toBe('Defense 4 — 0x Cross');
  });

  test('points the label at the alliance with more crossings', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { position5crossings: 1 },
          { position5crossings: 4 },
        )}
        match={match}
      />,
    );

    expect(
      within(rowFor('Defense 5')).getByRole('img', { name: 'Blue leads' }),
    ).toBeTruthy();
  });
});

describe('ScoreBreakdown2016 ranking points', () => {
  test.each([
    { label: 'Defenses Breached', field: 'teleopDefensesBreached' as const },
    { label: 'Tower Captured', field: 'teleopTowerCaptured' as const },
  ])(
    'checks $label when achieved and crosses it when not',
    ({ label, field }) => {
      render(
        <ScoreBreakdown2016
          scoreBreakdown={makeBreakdown({ [field]: true }, { [field]: false })}
          match={match}
        />,
      );

      expect(
        within(redCell(label)).getByRole('img', { name: 'Achieved' }),
      ).toBeTruthy();
      expect(
        within(blueCell(label)).getByRole('img', { name: 'Not achieved' }),
      ).toBeTruthy();
    },
  );

  test('shows the ranking points each alliance earned', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown({ tba_rpEarned: 4 }, { tba_rpEarned: 1 })}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+4 RP');
    expect(blueCell('RP').textContent).toBe('+1 RP');
  });

  test('shows zero ranking points when none are recorded', () => {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { tba_rpEarned: null },
          { tba_rpEarned: null },
        )}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+0 RP');
    expect(blueCell('RP').textContent).toBe('+0 RP');
  });
});

describe('ScoreBreakdown2016 fouls', () => {
  // Counts and foul points from 2016cmp_sf1m3; each alliance's foulPoints come from the other's fouls.
  function renderFouls() {
    render(
      <ScoreBreakdown2016
        scoreBreakdown={makeBreakdown(
          { foulCount: 1, techFoulCount: 1, foulPoints: 5 },
          { foulCount: 0, techFoulCount: 1, foulPoints: 10 },
        )}
        match={match}
      />,
    );
  }

  test('shows the fouls and tech fouls each alliance committed', () => {
    renderFouls();

    expect(redCell('Fouls / Tech Fouls Committed').textContent).toBe('1 / 1');
    expect(blueCell('Fouls / Tech Fouls Committed').textContent).toBe('0 / 1');
  });

  test('shows the foul points each alliance received', () => {
    renderFouls();

    expect(redCell('Foul Points Received').textContent).toBe('5');
    expect(blueCell('Foul Points Received').textContent).toBe('10');
  });
});
