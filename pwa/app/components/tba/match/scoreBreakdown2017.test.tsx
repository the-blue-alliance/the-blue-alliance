import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  Match,
  MatchScoreBreakdown2017,
  MatchScoreBreakdown2017Alliance,
  RobotAuto2017,
  Touchpad2017,
} from '~/api/tba/read';
import ScoreBreakdown2017 from '~/components/tba/match/scoreBreakdown2017';

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
  key: '2017nytr_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 320,
      team_keys: ['frc254', 'frc1678', 'frc971'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 180,
      team_keys: ['frc148', 'frc2056', 'frc118'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2017nytr',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2017Alliance> = {},
): MatchScoreBreakdown2017Alliance {
  return {
    autoPoints: 75,
    teleopPoints: 245,
    foulPoints: 5,
    adjustPoints: 0,
    totalPoints: 320,
    robot1Auto: RobotAuto2017.MOBILITY,
    robot2Auto: RobotAuto2017.MOBILITY,
    robot3Auto: RobotAuto2017.NONE,
    rotor1Auto: true,
    rotor2Auto: false,
    autoFuelLow: 3,
    autoFuelHigh: 10,
    autoMobilityPoints: 10,
    autoRotorPoints: 60,
    autoFuelPoints: 11,
    teleopFuelPoints: 25,
    teleopFuelLow: 6,
    teleopFuelHigh: 70,
    teleopRotorPoints: 120,
    kPaRankingPointAchieved: true,
    teleopTakeoffPoints: 100,
    kPaBonusPoints: 0,
    rotorBonusPoints: 0,
    rotor1Engaged: true,
    rotor2Engaged: true,
    rotor3Engaged: true,
    rotor4Engaged: false,
    rotorRankingPointAchieved: false,
    tba_rpEarned: 3,
    techFoulCount: 0,
    foulCount: 1,
    touchpadNear: Touchpad2017.READY_FOR_TAKEOFF,
    touchpadMiddle: Touchpad2017.NONE,
    touchpadFar: Touchpad2017.READY_FOR_TAKEOFF,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2017Alliance> = {},
  blue: Partial<MatchScoreBreakdown2017Alliance> = {},
): MatchScoreBreakdown2017 {
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

describe('ScoreBreakdown2017 auto mobility', () => {
  test('checks every robot that achieved mobility', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({
          robot1Auto: RobotAuto2017.MOBILITY,
          robot2Auto: RobotAuto2017.MOBILITY,
          robot3Auto: RobotAuto2017.MOBILITY,
          autoMobilityPoints: 15,
        })}
        match={match}
      />,
    );

    expect(
      within(redCell('Auto Mobility')).getAllByRole('img', {
        name: 'Achieved',
      }),
    ).toHaveLength(3);
  });

  test('crosses robots that did not move, are unknown, or are unreported', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown(
          {},
          {
            robot1Auto: RobotAuto2017.NONE,
            robot2Auto: RobotAuto2017.UNKNOWN,
            robot3Auto: undefined,
            autoMobilityPoints: 0,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Auto Mobility')).getAllByRole('img', {
        name: 'Not achieved',
      }),
    ).toHaveLength(3);
  });

  test('shows the mobility points alongside the checks', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({}, { autoMobilityPoints: 10 })}
        match={match}
      />,
    );

    expect(blueCell('Auto Mobility').textContent).toContain('(+10)');
  });

  // Wrong today: the third Auto Mobility ConditionalCheckmark receives
  // team_keys[2] === undefined and calls .substring on it, so the whole
  // breakdown throws for a two-team alliance.
  // Correct: the breakdown renders, showing the robots that exist.
  test('Bug #55: renders for a two-team alliance', () => {
    const twoTeamMatch: Match = {
      ...match,
      alliances: {
        ...match.alliances,
        red: { ...match.alliances.red, team_keys: ['frc254', 'frc1678'] },
      },
    };

    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({
          robot1Auto: RobotAuto2017.MOBILITY,
          robot2Auto: RobotAuto2017.MOBILITY,
          autoMobilityPoints: 10,
        })}
        match={twoTeamMatch}
      />,
    );

    expect(redCell('Auto Mobility').textContent).toContain('(+10)');
  });
});

describe('ScoreBreakdown2017 point rows', () => {
  test.each([
    { label: 'Auto Fuel High', field: 'autoFuelHigh' as const },
    { label: 'Auto Fuel Low', field: 'autoFuelLow' as const },
    { label: 'Auto Fuel Points', field: 'autoFuelPoints' as const },
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Teleop Fuel High', field: 'teleopFuelHigh' as const },
    { label: 'Teleop Fuel Low', field: 'teleopFuelLow' as const },
    { label: 'Teleop Fuel Points', field: 'teleopFuelPoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Adjustments', field: 'adjustPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('37');
    expect(blueCell(label).textContent).toBe('12');
  });

  test('shows 0 adjustments when the value is missing', () => {
    render(
      <ScoreBreakdown2017
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
      <ScoreBreakdown2017
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

describe('ScoreBreakdown2017 rotors', () => {
  test('shows only the two auto rotors in the auto row', () => {
    render(
      <ScoreBreakdown2017 scoreBreakdown={makeBreakdown()} match={match} />,
    );

    expect(within(redCell('Auto Rotors')).getByText('R1')).toBeTruthy();
    expect(within(redCell('Auto Rotors')).queryByText('R3')).toBeNull();
  });

  test('shows the auto rotor points', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ autoRotorPoints: 60 })}
        match={match}
      />,
    );

    expect(redCell('Auto Rotors').textContent).toContain('(+60)');
  });

  test('shows all four rotors in the teleop row', () => {
    render(
      <ScoreBreakdown2017 scoreBreakdown={makeBreakdown()} match={match} />,
    );

    expect(
      within(blueCell('Teleop Rotors'))
        .getAllByText(/^R[1-4]$/)
        .map((badge) => badge.textContent),
    ).toEqual(['R1', 'R2', 'R3', 'R4']);
  });

  test('shows the teleop rotor points', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({}, { teleopRotorPoints: 160 })}
        match={match}
      />,
    );

    expect(blueCell('Teleop Rotors').textContent).toContain('(+160)');
  });

  test('draws an engaged rotor differently from an idle one', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({
          rotor1Engaged: true,
          rotor2Engaged: false,
          rotor3Engaged: true,
          rotor4Engaged: false,
        })}
        match={match}
      />,
    );

    const cell = within(redCell('Teleop Rotors'));
    expect(cell.getByText('R1').className).not.toBe(
      cell.getByText('R2').className,
    );
    expect(cell.getByText('R3').className).toBe(cell.getByText('R1').className);
  });

  test('draws an auto rotor that turned differently from one that did not', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ rotor1Auto: true, rotor2Auto: false })}
        match={match}
      />,
    );

    const cell = within(redCell('Auto Rotors'));
    expect(cell.getByText('R1').className).not.toBe(
      cell.getByText('R2').className,
    );
  });
});

describe('ScoreBreakdown2017 takeoff', () => {
  test('labels the touchpads with the alliance team numbers', () => {
    render(
      <ScoreBreakdown2017 scoreBreakdown={makeBreakdown()} match={match} />,
    );

    const cell = within(redCell('Takeoff'));
    expect(cell.getByText('254')).toBeTruthy();
    expect(cell.getByText('1678')).toBeTruthy();
    expect(cell.getByText('971')).toBeTruthy();
  });

  test('shows the takeoff points', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ teleopTakeoffPoints: 150 })}
        match={match}
      />,
    );

    expect(redCell('Takeoff').textContent).toContain('(+150)');
  });

  test('draws a touchpad that is ready for takeoff differently from one that is not', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({
          touchpadNear: Touchpad2017.READY_FOR_TAKEOFF,
          touchpadMiddle: Touchpad2017.NONE,
          touchpadFar: undefined,
        })}
        match={match}
      />,
    );

    const cell = within(redCell('Takeoff'));
    expect(cell.getByText('254').className).not.toBe(
      cell.getByText('1678').className,
    );
    expect(cell.getByText('971').className).toBe(
      cell.getByText('1678').className,
    );
  });

  test('draws a ready touchpad the same way regardless of position', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown(
          {},
          {
            touchpadNear: Touchpad2017.NONE,
            touchpadMiddle: Touchpad2017.READY_FOR_TAKEOFF,
            touchpadFar: Touchpad2017.READY_FOR_TAKEOFF,
          },
        )}
        match={match}
      />,
    );

    const cell = within(blueCell('Takeoff'));
    expect(cell.getByText('2056').className).toBe(
      cell.getByText('118').className,
    );
  });
});

describe('ScoreBreakdown2017 ranking points', () => {
  test.each([
    { label: 'Pressure Reached', field: 'kPaRankingPointAchieved' as const },
    {
      label: 'All Rotors Engaged',
      field: 'rotorRankingPointAchieved' as const,
    },
  ])(
    'checks $label when achieved and crosses it when not',
    ({ label, field }) => {
      render(
        <ScoreBreakdown2017
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
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ tba_rpEarned: 4 }, { tba_rpEarned: 1 })}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+4 RP');
    expect(blueCell('RP').textContent).toBe('+1 RP');
  });

  test.each([
    { name: 'null', value: null },
    { name: 'missing', value: undefined },
  ])('shows zero ranking points when the value is $name', ({ value }) => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown(
          { tba_rpEarned: value },
          { tba_rpEarned: value },
        )}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+0 RP');
    expect(blueCell('RP').textContent).toBe('+0 RP');
  });
});

describe('ScoreBreakdown2017 fouls', () => {
  test("shows the opponent's fouls under each alliance", () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown(
          { foulCount: 2, techFoulCount: 1 },
          { foulCount: 4, techFoulCount: 0 },
        )}
        match={match}
      />,
    );

    expect(
      within(redCell('Fouls / Tech Fouls')).getByText('4 (+20)'),
    ).toBeTruthy();
    expect(
      within(blueCell('Fouls / Tech Fouls')).getByText('2 (+10)'),
    ).toBeTruthy();
  });

  test('values tech fouls at 25 points each', () => {
    render(
      <ScoreBreakdown2017
        scoreBreakdown={makeBreakdown({ techFoulCount: 2 }, {})}
        match={match}
      />,
    );

    expect(
      within(blueCell('Fouls / Tech Fouls')).getByText('2 (+50)'),
    ).toBeTruthy();
  });
});
