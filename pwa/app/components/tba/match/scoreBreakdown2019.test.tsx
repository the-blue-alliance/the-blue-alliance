import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  Bay2019,
  CompLevel,
  EndgameRobot2019,
  HabLine2019,
  Match,
  MatchScoreBreakdown2019,
  MatchScoreBreakdown2019Alliance,
  PreMatchBay2019,
} from '~/api/tba/read';
import ScoreBreakdown2019 from '~/components/tba/match/scoreBreakdown2019';

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
  key: '2019nytr_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 80,
      team_keys: ['frc254', 'frc1678', 'frc971'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 60,
      team_keys: ['frc148', 'frc2056', 'frc118'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2019nytr',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2019Alliance> = {},
): MatchScoreBreakdown2019Alliance {
  return {
    adjustPoints: 0,
    autoPoints: 15,
    bay1: Bay2019.PANEL_AND_CARGO,
    bay2: Bay2019.PANEL,
    bay3: Bay2019.NONE,
    bay4: Bay2019.PANEL_AND_CARGO,
    bay5: Bay2019.NONE,
    bay6: Bay2019.PANEL,
    bay7: Bay2019.NONE,
    bay8: Bay2019.NONE,
    cargoPoints: 30,
    completeRocketRankingPoint: false,
    completedRocketFar: false,
    completedRocketNear: false,
    endgameRobot1: EndgameRobot2019.HAB_LEVEL3,
    endgameRobot2: EndgameRobot2019.HAB_LEVEL1,
    endgameRobot3: EndgameRobot2019.NONE,
    foulCount: 1,
    foulPoints: 3,
    habClimbPoints: 15,
    habDockingRankingPoint: true,
    habLineRobot1: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
    habLineRobot2: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
    habLineRobot3: HabLine2019.CROSSED_HAB_LINE_IN_TELEOP,
    hatchPanelPoints: 20,
    lowLeftRocketFar: Bay2019.PANEL_AND_CARGO,
    lowLeftRocketNear: Bay2019.PANEL,
    lowRightRocketFar: Bay2019.NONE,
    lowRightRocketNear: Bay2019.PANEL_AND_CARGO,
    midLeftRocketFar: Bay2019.NONE,
    midLeftRocketNear: Bay2019.NONE,
    midRightRocketFar: Bay2019.PANEL,
    midRightRocketNear: Bay2019.NONE,
    preMatchBay1: PreMatchBay2019.PANEL,
    preMatchBay2: PreMatchBay2019.CARGO,
    preMatchBay3: PreMatchBay2019.UNKNOWN,
    preMatchBay6: PreMatchBay2019.PANEL,
    preMatchBay7: PreMatchBay2019.CARGO,
    preMatchBay8: PreMatchBay2019.UNKNOWN,
    preMatchLevelRobot1: EndgameRobot2019.HAB_LEVEL2,
    preMatchLevelRobot2: EndgameRobot2019.HAB_LEVEL1,
    preMatchLevelRobot3: EndgameRobot2019.HAB_LEVEL1,
    rp: 3,
    sandStormBonusPoints: 9,
    techFoulCount: 0,
    teleopPoints: 65,
    topLeftRocketFar: Bay2019.NONE,
    topLeftRocketNear: Bay2019.NONE,
    topRightRocketFar: Bay2019.NONE,
    topRightRocketNear: Bay2019.PANEL,
    totalPoints: 80,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2019Alliance> = {},
  blue: Partial<MatchScoreBreakdown2019Alliance> = {},
): MatchScoreBreakdown2019 {
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

describe('ScoreBreakdown2019 sandstorm', () => {
  test('checks every robot that crossed the HAB line in sandstorm', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({
          habLineRobot1: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
          habLineRobot2: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
          habLineRobot3: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
        })}
        match={match}
      />,
    );

    expect(
      within(redCell('Sandstorm Bonus')).getAllByRole('img', {
        name: 'Achieved',
      }),
    ).toHaveLength(3);
  });

  test('crosses robots that crossed in teleop, never crossed, or are unknown', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          {},
          {
            habLineRobot1: HabLine2019.CROSSED_HAB_LINE_IN_TELEOP,
            habLineRobot2: HabLine2019.NONE,
            habLineRobot3: HabLine2019.UNKNOWN,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Sandstorm Bonus')).getAllByRole('img', {
        name: 'Not achieved',
      }),
    ).toHaveLength(3);
  });

  test('shows the sandstorm bonus points alongside the checks', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({ sandStormBonusPoints: 12 })}
        match={match}
      />,
    );

    expect(redCell('Sandstorm Bonus').textContent).toContain('(+12)');
  });
});

describe('ScoreBreakdown2019 point rows', () => {
  test.each([
    { label: 'Hatch Panel Points', field: 'hatchPanelPoints' as const },
    { label: 'Cargo Points', field: 'cargoPoints' as const },
    { label: 'HAB Climb Points', field: 'habClimbPoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Adjustments', field: 'adjustPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('37');
    expect(blueCell(label).textContent).toBe('12');
  });

  test('shows 0 adjustments when the value is missing', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          { adjustPoints: undefined },
          { adjustPoints: undefined },
        )}
        match={match}
      />,
    );

    expect(redCell('Adjustments').textContent).toBe('0');
    expect(blueCell('Adjustments').textContent).toBe('0');
  });

  test('points the label at the alliance with the higher total', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          { totalPoints: 100 },
          { totalPoints: 140 },
        )}
        match={match}
      />,
    );

    expect(
      within(rowFor('Total Score')).getByRole('img', { name: 'Blue leads' }),
    ).toBeTruthy();
  });
});

describe('ScoreBreakdown2019 game pieces', () => {
  test('counts cargo ship panels and cargo across all eight bays', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({
          bay1: Bay2019.PANEL_AND_CARGO,
          bay2: Bay2019.PANEL,
          bay3: Bay2019.NONE,
          bay4: Bay2019.PANEL_AND_CARGO,
          bay5: Bay2019.NONE,
          bay6: Bay2019.PANEL,
          bay7: Bay2019.NONE,
          bay8: Bay2019.PANEL_AND_CARGO,
        })}
        match={match}
      />,
    );

    expect(redCell('Cargo Ship').textContent).toBe('5 HP / 3 Cargo');
  });

  test('shows an empty cargo ship as zero', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          {},
          {
            bay1: Bay2019.NONE,
            bay2: Bay2019.NONE,
            bay3: Bay2019.NONE,
            bay4: Bay2019.NONE,
            bay5: Bay2019.NONE,
            bay6: Bay2019.NONE,
            bay7: Bay2019.NONE,
            bay8: Bay2019.NONE,
          },
        )}
        match={match}
      />,
    );

    expect(blueCell('Cargo Ship').textContent).toBe('0 HP / 0 Cargo');
  });

  test('counts the near rocket as Rocket 1', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({
          topLeftRocketNear: Bay2019.PANEL_AND_CARGO,
          topRightRocketNear: Bay2019.PANEL_AND_CARGO,
          midLeftRocketNear: Bay2019.PANEL,
          midRightRocketNear: Bay2019.NONE,
          lowLeftRocketNear: Bay2019.PANEL,
          lowRightRocketNear: Bay2019.PANEL_AND_CARGO,
        })}
        match={match}
      />,
    );

    expect(redCell('Rocket 1').textContent).toBe('5 HP / 3 Cargo');
  });

  test('counts the far rocket as Rocket 2', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          {},
          {
            topLeftRocketFar: Bay2019.NONE,
            topRightRocketFar: Bay2019.NONE,
            midLeftRocketFar: Bay2019.PANEL,
            midRightRocketFar: Bay2019.PANEL,
            lowLeftRocketFar: Bay2019.PANEL_AND_CARGO,
            lowRightRocketFar: Bay2019.PANEL_AND_CARGO,
          },
        )}
        match={match}
      />,
    );

    expect(blueCell('Rocket 2').textContent).toBe('4 HP / 2 Cargo');
  });

  test('points a rocket row at the alliance with more game pieces', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          {
            topLeftRocketNear: Bay2019.NONE,
            topRightRocketNear: Bay2019.NONE,
            midLeftRocketNear: Bay2019.NONE,
            midRightRocketNear: Bay2019.NONE,
            lowLeftRocketNear: Bay2019.NONE,
            lowRightRocketNear: Bay2019.NONE,
          },
          { lowLeftRocketNear: Bay2019.PANEL },
        )}
        match={match}
      />,
    );

    expect(
      within(rowFor('Rocket 1')).getByRole('img', { name: 'Blue leads' }),
    ).toBeTruthy();
  });
});

describe('ScoreBreakdown2019 endgame', () => {
  // The 2019 game awarded 3 / 6 / 12 points for HAB levels 1 / 2 / 3, but the
  // component's ENDGAME_2019_POINTS table has 3 / 3 / 6. These cases pin the
  // values the component shows today, not the correct ones.
  test.each([
    { value: EndgameRobot2019.HAB_LEVEL3, expected: '254HAB 3 (+6)' },
    { value: EndgameRobot2019.HAB_LEVEL2, expected: '254HAB 2 (+3)' },
    { value: EndgameRobot2019.HAB_LEVEL1, expected: '254HAB 1 (+3)' },
    { value: EndgameRobot2019.NONE, expected: '254None (+0)' },
    { value: EndgameRobot2019.UNKNOWN, expected: '254Unknown (+0)' },
  ])('shows $value with its points for robot 1', ({ value, expected }) => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({ endgameRobot1: value })}
        match={match}
      />,
    );

    expect(redCell('Robot 1 Endgame').textContent).toBe(expected);
  });

  test('shows an unrecognised endgame value verbatim with zero points', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          {},
          { endgameRobot1: 'HabLevel4' as EndgameRobot2019 },
        )}
        match={match}
      />,
    );

    expect(blueCell('Robot 1 Endgame').textContent).toBe('148HabLevel4 (+0)');
  });

  test('shows the second robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          { endgameRobot2: EndgameRobot2019.HAB_LEVEL1 },
          { endgameRobot2: EndgameRobot2019.NONE },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 2 Endgame').textContent).toBe('1678HAB 1 (+3)');
    expect(blueCell('Robot 2 Endgame').textContent).toBe('2056None (+0)');
  });

  test('shows the third robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          { endgameRobot3: EndgameRobot2019.NONE },
          { endgameRobot3: EndgameRobot2019.HAB_LEVEL3 },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 3 Endgame').textContent).toBe('971None (+0)');
    expect(blueCell('Robot 3 Endgame').textContent).toBe('118HAB 3 (+6)');
  });
});

describe('ScoreBreakdown2019 ranking points', () => {
  test.each([
    { label: 'Complete Rocket', field: 'completeRocketRankingPoint' as const },
    { label: 'HAB Docking', field: 'habDockingRankingPoint' as const },
  ])(
    'checks $label when achieved and crosses it when not',
    ({ label, field }) => {
      render(
        <ScoreBreakdown2019
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
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({ rp: 4 }, { rp: 1 })}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+4 RP');
    expect(blueCell('RP').textContent).toBe('+1 RP');
  });
});

describe('ScoreBreakdown2019 fouls', () => {
  test("shows the opponent's fouls under each alliance", () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown(
          { foulCount: 2, techFoulCount: 1 },
          { foulCount: 4, techFoulCount: 0 },
        )}
        match={match}
      />,
    );

    expect(
      within(redCell('Fouls / Tech Fouls')).getByText('4 (+12)'),
    ).toBeTruthy();
    expect(
      within(blueCell('Fouls / Tech Fouls')).getByText('2 (+6)'),
    ).toBeTruthy();
  });

  test('values tech fouls at 10 points each', () => {
    render(
      <ScoreBreakdown2019
        scoreBreakdown={makeBreakdown({ techFoulCount: 2 }, {})}
        match={match}
      />,
    );

    expect(
      within(blueCell('Fouls / Tech Fouls')).getByText('2 (+20)'),
    ).toBeTruthy();
  });
});
