import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  EndgameRobot2020,
  EndgameRungIsLevel2020,
  InitLineRobot2020,
  Match,
  MatchScoreBreakdown2020,
  MatchScoreBreakdown2020Alliance,
  Stage3TargetColor2020,
} from '~/api/tba/read';
import ScoreBreakdown2020 from '~/components/tba/match/scoreBreakdown2020';

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
  key: '2020nytr_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 150,
      team_keys: ['frc254', 'frc1678', 'frc971'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 90,
      team_keys: ['frc148', 'frc2056', 'frc118'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2020nytr',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2020Alliance> = {},
): MatchScoreBreakdown2020Alliance {
  return {
    initLineRobot1: InitLineRobot2020.EXITED,
    endgameRobot1: EndgameRobot2020.HANG,
    initLineRobot2: InitLineRobot2020.EXITED,
    endgameRobot2: EndgameRobot2020.PARK,
    initLineRobot3: InitLineRobot2020.NONE,
    endgameRobot3: EndgameRobot2020.NONE,
    autoCellsBottom: 2,
    autoCellsOuter: 5,
    autoCellsInner: 1,
    teleopCellsBottom: 4,
    teleopCellsOuter: 20,
    teleopCellsInner: 6,
    stage1Activated: true,
    stage2Activated: true,
    stage3Activated: false,
    stage3TargetColor: Stage3TargetColor2020.UNKNOWN,
    endgameRungIsLevel: EndgameRungIsLevel2020.IS_LEVEL,
    autoInitLinePoints: 10,
    autoCellPoints: 30,
    autoPoints: 40,
    teleopCellPoints: 62,
    controlPanelPoints: 10,
    endgamePoints: 45,
    teleopPoints: 117,
    shieldOperationalRankingPoint: false,
    shieldEnergizedRankingPoint: true,
    tba_shieldEnergizedRankingPointFromFoul: false,
    tba_numRobotsHanging: 1,
    foulCount: 1,
    techFoulCount: 0,
    adjustPoints: 0,
    foulPoints: 3,
    rp: 3,
    totalPoints: 150,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2020Alliance> = {},
  blue: Partial<MatchScoreBreakdown2020Alliance> = {},
): MatchScoreBreakdown2020 {
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

describe('ScoreBreakdown2020 initiation line', () => {
  test('checks every robot that exited the initiation line', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({
          initLineRobot1: InitLineRobot2020.EXITED,
          initLineRobot2: InitLineRobot2020.EXITED,
          initLineRobot3: InitLineRobot2020.EXITED,
        })}
        match={match}
      />,
    );

    expect(
      within(redCell('Initiation Line')).getAllByRole('img', {
        name: 'Achieved',
      }),
    ).toHaveLength(3);
  });

  test('crosses every robot that stayed on the initiation line', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          {},
          {
            initLineRobot1: InitLineRobot2020.NONE,
            initLineRobot2: InitLineRobot2020.NONE,
            initLineRobot3: InitLineRobot2020.NONE,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Initiation Line')).getAllByRole('img', {
        name: 'Not achieved',
      }),
    ).toHaveLength(3);
  });

  test('shows the initiation line points alongside the checks', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({ autoInitLinePoints: 15 })}
        match={match}
      />,
    );

    expect(redCell('Initiation Line').textContent).toContain('(+15)');
  });
});

describe('ScoreBreakdown2020 point rows', () => {
  test.each([
    { label: 'Auto Bottom Port', field: 'autoCellsBottom' as const },
    { label: 'Auto Outer Port', field: 'autoCellsOuter' as const },
    { label: 'Auto Inner Port', field: 'autoCellsInner' as const },
    { label: 'Auto Cell Points', field: 'autoCellPoints' as const },
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Teleop Bottom Port', field: 'teleopCellsBottom' as const },
    { label: 'Teleop Outer Port', field: 'teleopCellsOuter' as const },
    { label: 'Teleop Inner Port', field: 'teleopCellsInner' as const },
    { label: 'Teleop Cell Points', field: 'teleopCellPoints' as const },
    { label: 'Endgame Points', field: 'endgamePoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Adjustments', field: 'adjustPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('37');
    expect(blueCell(label).textContent).toBe('12');
  });

  test('shows 0 adjustments when the value is missing', () => {
    render(
      <ScoreBreakdown2020
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
      <ScoreBreakdown2020
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

describe('ScoreBreakdown2020 control panel', () => {
  test('shows all three stages', () => {
    render(
      <ScoreBreakdown2020 scoreBreakdown={makeBreakdown()} match={match} />,
    );

    expect(
      within(redCell('Control Panel'))
        .getAllByText(/^S[1-3]$/)
        .map((badge) => badge.textContent),
    ).toEqual(['S1', 'S2', 'S3']);
  });

  test('shows the control panel points', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({}, { controlPanelPoints: 20 })}
        match={match}
      />,
    );

    expect(within(blueCell('Control Panel')).getByText('(+20)')).toBeTruthy();
  });

  test('draws an activated stage differently from an inactive one', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({
          stage1Activated: true,
          stage2Activated: false,
          stage3Activated: true,
        })}
        match={match}
      />,
    );

    const cell = within(redCell('Control Panel'));
    expect(cell.getByText('S1').className).not.toBe(
      cell.getByText('S2').className,
    );
    expect(cell.getByText('S3').className).toBe(cell.getByText('S1').className);
  });

  test('draws every stage the same when none are activated', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          {},
          {
            stage1Activated: false,
            stage2Activated: false,
            stage3Activated: false,
          },
        )}
        match={match}
      />,
    );

    const cell = within(blueCell('Control Panel'));
    expect(cell.getByText('S1').className).toBe(cell.getByText('S2').className);
    expect(cell.getByText('S2').className).toBe(cell.getByText('S3').className);
  });
});

describe('ScoreBreakdown2020 endgame', () => {
  test.each([
    { value: EndgameRobot2020.HANG, expected: '254Hang (+25)' },
    { value: EndgameRobot2020.PARK, expected: '254Park (+5)' },
    { value: EndgameRobot2020.NONE, expected: '254None (+0)' },
  ])('shows $value with its points for robot 1', ({ value, expected }) => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({ endgameRobot1: value })}
        match={match}
      />,
    );

    expect(redCell('Robot 1 Endgame').textContent).toBe(expected);
  });

  test('shows an unrecognised endgame value verbatim with zero points', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          {},
          { endgameRobot1: 'Unknown' as EndgameRobot2020 },
        )}
        match={match}
      />,
    );

    expect(blueCell('Robot 1 Endgame').textContent).toBe('148Unknown (+0)');
  });

  test('shows the second robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          { endgameRobot2: EndgameRobot2020.PARK },
          { endgameRobot2: EndgameRobot2020.HANG },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 2 Endgame').textContent).toBe('1678Park (+5)');
    expect(blueCell('Robot 2 Endgame').textContent).toBe('2056Hang (+25)');
  });

  test('shows the third robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          { endgameRobot3: EndgameRobot2020.NONE },
          { endgameRobot3: EndgameRobot2020.HANG },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 3 Endgame').textContent).toBe('971None (+0)');
    expect(blueCell('Robot 3 Endgame').textContent).toBe('118Hang (+25)');
  });

  test('checks a level rung and crosses one that is not level', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          { endgameRungIsLevel: EndgameRungIsLevel2020.IS_LEVEL },
          { endgameRungIsLevel: EndgameRungIsLevel2020.NOT_LEVEL },
        )}
        match={match}
      />,
    );

    expect(
      within(redCell('Rung Level')).getByRole('img', { name: 'Achieved' }),
    ).toBeTruthy();
    expect(
      within(blueCell('Rung Level')).getByRole('img', {
        name: 'Not achieved',
      }),
    ).toBeTruthy();
  });
});

describe('ScoreBreakdown2020 ranking points', () => {
  test.each([
    {
      label: 'Shield Operational',
      field: 'shieldOperationalRankingPoint' as const,
    },
    {
      label: 'Shield Energized',
      field: 'shieldEnergizedRankingPoint' as const,
    },
  ])(
    'checks $label when achieved and crosses it when not',
    ({ label, field }) => {
      render(
        <ScoreBreakdown2020
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
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({ rp: 4 }, { rp: 1 })}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+4 RP');
    expect(blueCell('RP').textContent).toBe('+1 RP');
  });

  test('shows zero ranking points when the value is missing', () => {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown({ rp: undefined }, { rp: undefined })}
        match={match}
      />,
    );

    expect(redCell('RP').textContent).toBe('+0 RP');
    expect(blueCell('RP').textContent).toBe('+0 RP');
  });
});

describe('ScoreBreakdown2020 fouls', () => {
  // Counts and foul points from 2020scmb_qm92; each alliance's foulPoints come from the other's fouls.
  function renderFouls() {
    render(
      <ScoreBreakdown2020
        scoreBreakdown={makeBreakdown(
          { foulCount: 2, techFoulCount: 1, foulPoints: 15 },
          { foulCount: 0, techFoulCount: 1, foulPoints: 21 },
        )}
        match={match}
      />,
    );
  }

  test('shows the fouls and tech fouls each alliance committed', () => {
    renderFouls();

    expect(redCell('Fouls / Tech Fouls Committed').textContent).toBe('2 / 1');
    expect(blueCell('Fouls / Tech Fouls Committed').textContent).toBe('0 / 1');
  });

  test('shows the foul points each alliance received', () => {
    renderFouls();

    expect(redCell('Foul Points Received').textContent).toBe('15');
    expect(blueCell('Foul Points Received').textContent).toBe('21');
  });
});
