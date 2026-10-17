import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type EliminationAlliance,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({ teamKey }: { teamKey: string }) => (
    <a href={`/team/${teamKey}`}>{teamKey.substring(3)}</a>
  ),
}));

function alliance(
  overrides: Partial<EliminationAlliance>,
): EliminationAlliance {
  return { declines: [], picks: [], ...overrides };
}

function status(
  level: CompLevel,
  result: 'eliminated' | 'playing' | 'won',
): EliminationAlliance['status'] {
  return {
    playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
    level,
    record: null,
    current_level_record: null,
    status: result,
  };
}

function final(red: string[], blue: string[], winner: AllianceColor): Match {
  return {
    key: '2026test_f1m1',
    event_key: '2026test',
    comp_level: CompLevel.F,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: {
        score: 100,
        team_keys: red,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: 90,
        team_keys: blue,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance: winner,
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  };
}

function headers() {
  return screen.getAllByRole('columnheader').map((h) => h.textContent);
}

describe('AllianceSelectionTable', () => {
  test('renders alliances with winners, finalists, and missing picks', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[
          alliance({
            name: 'Alliance 1',
            picks: ['frc254', 'frc604', 'frc1678', 'frc4414'],
          }),
          alliance({
            name: 'Alliance 2',
            picks: ['frc1', 'frc2', 'frc3'],
          }),
          alliance({
            name: 'Custom Name',
            picks: ['frc4', 'frc5'],
          }),
          alliance({ picks: ['frc6'] }),
        ]}
        eventOver
        matches={[
          final(
            ['frc254', 'frc604', 'frc1678'],
            ['frc1', 'frc2', 'frc3'],
            AllianceColor.RED,
          ),
        ]}
      />,
    );
    expect(headers()).toEqual([
      'Alliance',
      'Captain',
      'Pick 1',
      'Pick 2',
      'Pick 3',
    ]);
    const [, winner, finalist, other, unnamed] = screen.getAllByRole('row');
    expect(winner.className).toContain('bg-yellow-100!');
    expect(winner.querySelector('svg')).toBeTruthy();
    expect(within(winner).getAllByRole('cell')[0].textContent).toBe('1');
    expect(finalist.className).toContain('bg-neutral-100!');
    expect(
      within(other)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['Custom Name', '4', '5', '-', '-']);
    expect(other.className).not.toContain('!');
    expect(
      within(unnamed)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['4', '6', '-', '-', '-']);
  });

  test('shows a trophy only for the finals winner when statuses say semifinal alliances won', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[
          alliance({
            picks: ['frc694', 'frc1768', 'frc11175'],
            status: status(CompLevel.F, 'playing'),
          }),
          alliance({
            picks: ['frc48', 'frc5813', 'frc271'],
            status: status(CompLevel.F, 'playing'),
          }),
          alliance({
            picks: ['frc1922', 'frc238', 'frc1735'],
            status: status(CompLevel.SF, 'won'),
          }),
        ]}
        eventOver
        matches={[
          final(
            ['frc11175', 'frc1768', 'frc694'],
            ['frc271', 'frc5813', 'frc48'],
            AllianceColor.RED,
          ),
        ]}
      />,
    );
    const [, ...rows] = screen.getAllByRole('row');
    expect(rows.map((row) => !!row.querySelector('svg'))).toEqual([
      true,
      false,
      false,
    ]);
  });

  test('shows_remapped_team_in_picks', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        remapTeams={{ frc9997: 'frc3467B' }}
        alliances={[
          alliance({
            name: 'Alliance 2',
            picks: ['frc9997', 'frc1073', 'frc1350'],
          }),
        ]}
        eventOver={false}
        matches={[]}
      />,
    );
    const [, row] = screen.getAllByRole('row');
    expect(
      within(row)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['2', '3467B', '1073', '1350']);
  });

  test('uses three columns when no alliance has picks', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[alliance({})]}
        eventOver={false}
        matches={[]}
      />,
    );
    expect(headers()).toEqual(['Alliance', 'Captain', 'Pick 1', 'Pick 2']);
  });

  test('an empty alliance list falls back to the default three team columns', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[]}
        eventOver={false}
        matches={[]}
      />,
    );
    expect(headers()).toEqual(['Alliance', 'Captain', 'Pick 1', 'Pick 2']);
  });

  test('renders a single-team alliance without pick columns', () => {
    render(
      <AllianceSelectionTable
        year={2026}
        alliances={[alliance({ name: 'Alliance 1', picks: ['frc254'] })]}
        eventOver={false}
        matches={[]}
      />,
    );
    expect(headers()).toEqual(['Alliance', 'Captain']);
  });
});
