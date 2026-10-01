import { render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import type { PlayoffAdvancement } from '~/api/tba/read';
import RoundRobinRankingsTable from '~/components/tba/roundRobinRankingsTable';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({ teamKey }: { teamKey: string }) => (
    <a href={`/team/${teamKey}`}>{teamKey.substring(3)}</a>
  ),
}));

function cells(row: HTMLElement) {
  return within(row)
    .getAllByRole('cell')
    .map((c) => c.textContent);
}

describe('RoundRobinRankingsTable', () => {
  test('renders rankings with tiebreakers and advancement', () => {
    const advancement: PlayoffAdvancement = {
      level: 'sf',
      level_name: 'Round Robin Semifinals',
      type: 'round_robin',
      sort_order_info: [
        { name: 'Points', type: 'int', precision: 0 },
        { name: 'Auto', type: 'int', precision: 0 },
      ],
      extra_stats_info: [{ name: 'Advance', type: 'bool', precision: 0 }],
      rankings: [
        {
          team_keys: ['frc254', 'frc604', 'frc1678'],
          alliance_name: 'Alliance 1',
          rank: 1,
          record: { wins: 3, losses: 0, ties: 1 },
          matches_played: 4,
          sort_orders: [10, 40],
          extra_stats: [1],
        },
        {
          team_keys: ['frc1'],
          alliance_name: 'Alliance 2',
          rank: null,
          record: null,
          matches_played: 4,
          sort_orders: [4, 20],
          extra_stats: [0],
        },
      ],
    } as PlayoffAdvancement;
    render(<RoundRobinRankingsTable advancement={advancement} year={2015} />);
    expect(
      screen.getByRole('heading', { name: 'Round Robin Semifinals' }),
    ).toBeTruthy();
    expect(
      screen.getAllByRole('columnheader').map((h) => h.textContent),
    ).toEqual([
      'Rank',
      'Alliance',
      'Teams',
      'Record',
      'Points',
      'Auto',
      'Advance',
    ]);
    const [, first, second] = screen.getAllByRole('row');
    expect(cells(first)).toEqual([
      '1',
      'Alliance 1',
      '254, 604, 1678',
      '3-0-1',
      '10',
      '40',
      '',
    ]);
    expect(within(first).getByLabelText('Advances')).toBeTruthy();
    expect(cells(second)).toEqual(['2', 'Alliance 2', '1', '—', '4', '20', '']);
    expect(within(second).queryByLabelText('Advances')).toBeNull();
  });

  test('falls back to Points without sort info, advancement, or rankings', () => {
    render(
      <RoundRobinRankingsTable
        advancement={{
          level: 'f',
          level_name: 'Finals',
          type: 'round_robin',
          sort_order_info: [],
          extra_stats_info: [],
          rankings: null,
        }}
        year={2015}
      />,
    );
    expect(
      screen.getAllByRole('columnheader').map((h) => h.textContent),
    ).toEqual(['Rank', 'Alliance', 'Teams', 'Record', 'Points']);
    expect(screen.getAllByRole('row')).toHaveLength(1);
  });
});
