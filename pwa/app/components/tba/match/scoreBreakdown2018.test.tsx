import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  AutoRobot2018,
  CompLevel,
  EndgameRobot2018,
  Match,
  MatchScoreBreakdown2018,
  MatchScoreBreakdown2018Alliance,
} from '~/api/tba/read';
import ScoreBreakdown2018 from '~/components/tba/match/scoreBreakdown2018';

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
  key: '2018nytr_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 420,
      team_keys: ['frc254', 'frc1678', 'frc971'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 300,
      team_keys: ['frc148', 'frc2056', 'frc118'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2018nytr',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2018Alliance> = {},
): MatchScoreBreakdown2018Alliance {
  return {
    adjustPoints: 0,
    autoOwnershipPoints: 30,
    autoPoints: 45,
    autoQuestRankingPoint: true,
    autoRobot1: AutoRobot2018.AUTO_RUN,
    autoRobot2: AutoRobot2018.AUTO_RUN,
    autoRobot3: AutoRobot2018.NONE,
    autoRunPoints: 10,
    autoScaleOwnershipSec: 10,
    autoSwitchAtZero: true,
    autoSwitchOwnershipSec: 5,
    endgamePoints: 65,
    endgameRobot1: EndgameRobot2018.CLIMBING,
    endgameRobot2: EndgameRobot2018.LEVITATE,
    endgameRobot3: EndgameRobot2018.PARKING,
    faceTheBossRankingPoint: true,
    foulCount: 1,
    foulPoints: 5,
    rp: 4,
    techFoulCount: 0,
    teleopOwnershipPoints: 220,
    teleopPoints: 375,
    teleopScaleBoostSec: 10,
    teleopScaleForceSec: 0,
    teleopScaleOwnershipSec: 120,
    teleopSwitchBoostSec: 0,
    teleopSwitchForceSec: 0,
    teleopSwitchOwnershipSec: 90,
    totalPoints: 420,
    vaultBoostPlayed: 2,
    vaultBoostTotal: 3,
    vaultForcePlayed: 1,
    vaultForceTotal: 2,
    vaultLevitatePlayed: 3,
    vaultLevitateTotal: 3,
    vaultPoints: 40,
    tba_gameData: 'LRL',
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2018Alliance> = {},
  blue: Partial<MatchScoreBreakdown2018Alliance> = {},
): MatchScoreBreakdown2018 {
  return { red: makeAlliance(red), blue: makeAlliance(blue) };
}

function rowFor(label: string, index = 0): HTMLElement {
  const row = screen.getAllByText(label)[index].closest('tr');
  if (!row) {
    throw new Error(`No row labelled ${label}`);
  }
  return row;
}

function redCell(label: string, index = 0): HTMLElement {
  return within(rowFor(label, index)).getAllByRole('cell')[0];
}

function blueCell(label: string, index = 0): HTMLElement {
  return within(rowFor(label, index)).getAllByRole('cell')[2];
}

describe('ScoreBreakdown2018 auto run', () => {
  test('checks every robot that completed the auto run', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({
          autoRobot1: AutoRobot2018.AUTO_RUN,
          autoRobot2: AutoRobot2018.AUTO_RUN,
          autoRobot3: AutoRobot2018.AUTO_RUN,
        })}
        match={match}
      />,
    );

    expect(
      within(redCell('Auto Run')).getAllByRole('img', { name: 'Achieved' }),
    ).toHaveLength(3);
  });

  test('crosses robots that stayed put or are unreported', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          {},
          {
            autoRobot1: AutoRobot2018.NONE,
            autoRobot2: undefined,
            autoRobot3: AutoRobot2018.NONE,
          },
        )}
        match={match}
      />,
    );

    expect(
      within(blueCell('Auto Run')).getAllByRole('img', {
        name: 'Not achieved',
      }),
    ).toHaveLength(3);
  });

  test('labels each auto run badge with its team number', () => {
    render(
      <ScoreBreakdown2018 scoreBreakdown={makeBreakdown()} match={match} />,
    );

    const cell = within(blueCell('Auto Run'));
    expect(cell.getByText('148')).toBeTruthy();
    expect(cell.getByText('2056')).toBeTruthy();
    expect(cell.getByText('118')).toBeTruthy();
  });

  test('shows the auto run points for each alliance', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { autoRunPoints: 15 },
          { autoRunPoints: 5 },
        )}
        match={match}
      />,
    );

    expect(within(redCell('Auto Run')).getByText('15')).toBeTruthy();
    expect(within(blueCell('Auto Run')).getByText('5')).toBeTruthy();
  });
});

describe('ScoreBreakdown2018 point rows', () => {
  test.each([
    { label: 'Auto Scale Owned', field: 'autoScaleOwnershipSec' as const },
    { label: 'Auto Switch Owned', field: 'autoSwitchOwnershipSec' as const },
    { label: 'Total Auto', field: 'autoPoints' as const },
    { label: 'Vault Points', field: 'vaultPoints' as const },
    { label: 'Endgame Points', field: 'endgamePoints' as const },
    { label: 'Total Teleop', field: 'teleopPoints' as const },
    { label: 'Total Score', field: 'totalPoints' as const },
  ])('shows each alliance value for $label', ({ label, field }) => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({ [field]: 37 }, { [field]: 12 })}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('37');
    expect(blueCell(label).textContent).toBe('12');
  });

  test('shows auto ownership points in the first Ownership Points row', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { autoOwnershipPoints: 30, teleopOwnershipPoints: 200 },
          { autoOwnershipPoints: 0, teleopOwnershipPoints: 150 },
        )}
        match={match}
      />,
    );

    expect(redCell('Ownership Points', 0).textContent).toBe('30');
    expect(blueCell('Ownership Points', 0).textContent).toBe('0');
  });

  test('shows teleop ownership points in the second Ownership Points row', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { autoOwnershipPoints: 30, teleopOwnershipPoints: 200 },
          { autoOwnershipPoints: 0, teleopOwnershipPoints: 150 },
        )}
        match={match}
      />,
    );

    expect(redCell('Ownership Points', 1).textContent).toBe('200');
    expect(blueCell('Ownership Points', 1).textContent).toBe('150');
  });

  test('shows scale ownership plus boost seconds', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({
          teleopScaleOwnershipSec: 120,
          teleopScaleBoostSec: 10,
        })}
        match={match}
      />,
    );

    expect(redCell('Scale Owned + Boost').textContent).toBe('120 + 10');
  });

  test('shows switch ownership plus boost seconds', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          {},
          { teleopSwitchOwnershipSec: 90, teleopSwitchBoostSec: 20 },
        )}
        match={match}
      />,
    );

    expect(blueCell('Switch Ownership + Boost').textContent).toBe('90 + 20');
  });

  test.each([
    {
      label: 'Scale Owned + Boost',
      fields: ['teleopScaleOwnershipSec', 'teleopScaleBoostSec'] as const,
    },
    {
      label: 'Switch Ownership + Boost',
      fields: ['teleopSwitchOwnershipSec', 'teleopSwitchBoostSec'] as const,
    },
  ])(
    'shows zero seconds for $label when values are missing',
    ({ label, fields }) => {
      render(
        <ScoreBreakdown2018
          scoreBreakdown={makeBreakdown({
            [fields[0]]: undefined,
            [fields[1]]: undefined,
          })}
          match={match}
        />,
      );

      expect(redCell(label).textContent).toBe('0 + 0');
    },
  );

  test('points the scale row at the alliance with more combined seconds', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { teleopScaleOwnershipSec: 50, teleopScaleBoostSec: 0 },
          { teleopScaleOwnershipSec: 40, teleopScaleBoostSec: 20 },
        )}
        match={match}
      />,
    );

    expect(
      within(rowFor('Scale Owned + Boost')).getByRole('img', {
        name: 'Blue leads',
      }),
    ).toBeTruthy();
  });

  test.each([
    {
      label: 'Force Cubes Total (Played)',
      total: 'vaultForceTotal' as const,
      played: 'vaultForcePlayed' as const,
    },
    {
      label: 'Levitate Cubes Total (Played)',
      total: 'vaultLevitateTotal' as const,
      played: 'vaultLevitatePlayed' as const,
    },
    {
      label: 'Boost Cubes Total (Played)',
      total: 'vaultBoostTotal' as const,
      played: 'vaultBoostPlayed' as const,
    },
  ])('shows cubes total and played for $label', ({ label, total, played }) => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { [total]: 3, [played]: 2 },
          { [total]: 1, [played]: 0 },
        )}
        match={match}
      />,
    );

    expect(redCell(label).textContent).toBe('3 (2)');
    expect(blueCell(label).textContent).toBe('1 (0)');
  });
});

describe('ScoreBreakdown2018 endgame', () => {
  test.each([
    { value: EndgameRobot2018.CLIMBING, expected: '254Climbing (+30)' },
    { value: EndgameRobot2018.LEVITATE, expected: '254Levitate (+30)' },
    { value: EndgameRobot2018.PARKING, expected: '254Parking (+5)' },
    { value: EndgameRobot2018.NONE, expected: '254None (+0)' },
    { value: EndgameRobot2018.UNKNOWN, expected: '254Unknown (+0)' },
  ])('shows $value with its points for robot 1', ({ value, expected }) => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({ endgameRobot1: value })}
        match={match}
      />,
    );

    expect(redCell('Robot 1 Endgame').textContent).toBe(expected);
  });

  test('shows zero points when an endgame is unreported', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({}, { endgameRobot1: undefined })}
        match={match}
      />,
    );

    expect(blueCell('Robot 1 Endgame').textContent).toBe('148 (+0)');
  });

  test('shows the second robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { endgameRobot2: EndgameRobot2018.PARKING },
          { endgameRobot2: undefined },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 2 Endgame').textContent).toBe('1678Parking (+5)');
    expect(blueCell('Robot 2 Endgame').textContent).toBe('2056 (+0)');
  });

  test('shows the third robot endgame for each alliance', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { endgameRobot3: undefined },
          { endgameRobot3: EndgameRobot2018.CLIMBING },
        )}
        match={match}
      />,
    );

    expect(redCell('Robot 3 Endgame').textContent).toBe('971 (+0)');
    expect(blueCell('Robot 3 Endgame').textContent).toBe('118Climbing (+30)');
  });
});

describe('ScoreBreakdown2018 fouls', () => {
  // Both alliances get identical counts here: which alliance's counts belong
  // under which column is Bug #54, covered by its own failing-test PR.
  test('values fouls at 5 points each', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { foulCount: 2, techFoulCount: 0 },
          { foulCount: 2, techFoulCount: 0 },
        )}
        match={match}
      />,
    );

    expect(within(redCell('Fouls Received')).getByText('2 (+10)')).toBeTruthy();
    expect(
      within(blueCell('Fouls Received')).getByText('2 (+10)'),
    ).toBeTruthy();
  });

  test('values tech fouls at 25 points each', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { techFoulCount: 2 },
          { techFoulCount: 2 },
        )}
        match={match}
      />,
    );

    expect(within(redCell('Fouls Received')).getByText('2 (+50)')).toBeTruthy();
  });
});

describe('ScoreBreakdown2018 adjustments', () => {
  test('shows the adjustments row when both alliances were adjusted', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { adjustPoints: 5 },
          { adjustPoints: -5 },
        )}
        match={match}
      />,
    );

    expect(redCell('Adjustments').textContent).toBe('5');
    expect(blueCell('Adjustments').textContent).toBe('-5');
  });

  test('hides the adjustments row when neither alliance was adjusted', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown({ adjustPoints: 0 }, { adjustPoints: 0 })}
        match={match}
      />,
    );

    expect(screen.queryByText('Adjustments')).toBeNull();
  });

  test('hides the adjustments row when adjustments are unreported', () => {
    render(
      <ScoreBreakdown2018
        scoreBreakdown={makeBreakdown(
          { adjustPoints: undefined },
          { adjustPoints: undefined },
        )}
        match={match}
      />,
    );

    expect(screen.queryByText('Adjustments')).toBeNull();
  });
});
