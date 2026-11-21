import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { type EventRanking } from '~/api/tba/read';
import RankingsTable from '~/components/tba/rankingsTable';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({
    teamKey,
    year,
    isWinner,
    isCaptain,
  }: {
    teamKey: string;
    year: number;
    isWinner?: boolean;
    isCaptain?: boolean;
  }) => (
    <a
      href={`/team/${teamKey.substring(3)}/${year}`}
      data-winner={isWinner}
      data-captain={isCaptain}
    >
      {teamKey.substring(3)}
    </a>
  ),
}));

type Ranking = EventRanking['rankings'][number];

function makeRanking(overrides: Partial<Ranking> & { rank: number }): Ranking {
  return {
    team_key: `frc${overrides.rank}`,
    matches_played: 10,
    qual_average: null,
    extra_stats: [1.5],
    sort_orders: [2.345, 100.5],
    record: { wins: 5, losses: 5, ties: 0 },
    dq: 0,
    ...overrides,
  };
}

const rankings: EventRanking = {
  rankings: [
    makeRanking({ rank: 1, record: { wins: 10, losses: 0, ties: 0 } }),
    makeRanking({ rank: 2, record: { wins: 5, losses: 5, ties: 0 } }),
    makeRanking({ rank: 3, record: null }),
  ],
  sort_order_info: [
    { name: 'Ranking Score', precision: 2 },
    { name: 'Avg Match', precision: 0 },
  ],
  extra_stats_info: [{ name: 'Total Ranking Points*', precision: 0 }],
};

function bodyRows() {
  return screen.getAllByRole('row').slice(1);
}

describe('RankingsTable', () => {
  test('renders a column for each sort order and extra stat', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    const headers = screen
      .getAllByRole('columnheader')
      .map((h) => h.textContent);
    expect(headers).toEqual([
      'Rank',
      'Team',
      'Ranking Score',
      'Avg Match',
      'Record (W-L-T)',
      'DQ',
      'Played',
      'Total Ranking Points*',
    ]);
  });

  test('formats sort orders to their precision and records as W-L-T', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    const cells = within(bodyRows()[0])
      .getAllByRole('cell')
      .map((c) => c.textContent);
    expect(cells).toEqual([
      '1',
      '1',
      '2.35',
      '101',
      '10-0-0',
      '0',
      '10',
      '1.5',
    ]);
  });

  test('marks winners and captains on the team link', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={['frc1']}
        captains={['frc1', 'frc2']}
        year={2026}
      />,
    );

    const winner = screen.getByRole('link', { name: '1' });
    expect(winner.getAttribute('data-winner')).toBe('true');
    expect(winner.getAttribute('data-captain')).toBe('true');
    expect(winner.getAttribute('href')).toBe('/team/1/2026');

    const captainOnly = screen.getByRole('link', { name: '2' });
    expect(captainOnly.getAttribute('data-winner')).toBe('false');
    expect(captainOnly.getAttribute('data-captain')).toBe('true');
  });

  test('highlights winner rows', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={['frc2']}
        captains={[]}
        year={2026}
      />,
    );

    const rows = bodyRows();
    expect(rows[1].className).toContain('bg-yellow-100!');
    expect(rows[0].className).not.toContain('bg-yellow-100!');
  });

  test('shows the event winner key when the event has winners', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={['frc1']}
        captains={[]}
        year={2026}
      />,
    );

    expect(screen.getByText('Event winner')).toBeTruthy();
  });

  test('shows the alliance captain key when the event has captains', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={[]}
        captains={['frc1']}
        year={2026}
      />,
    );

    expect(screen.getByText('Alliance captain')).toBeTruthy();
  });

  test('omits the event winner key when the event has no winners', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={[]}
        captains={['frc1']}
        year={2026}
      />,
    );

    expect(screen.queryByText('Event winner')).toBeNull();
  });

  test('omits the key when the event has no winners or captains', () => {
    render(
      <RankingsTable
        rankings={rankings}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    expect(screen.queryByRole('list', { name: 'Key' })).toBeNull();
  });

  test('omits the record column when the first team has no record', () => {
    render(
      <RankingsTable
        rankings={{
          ...rankings,
          rankings: [makeRanking({ rank: 1, record: null })],
        }}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    expect(screen.queryByText('Record (W-L-T)')).toBeNull();
  });

  test('tolerates missing sort order info', () => {
    render(
      <RankingsTable
        rankings={{ ...rankings, sort_order_info: null }}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    expect(screen.queryByText('Ranking Score')).toBeNull();
    expect(screen.getByText('Record (W-L-T)')).toBeTruthy();
  });

  test('sorts by team number', () => {
    render(
      <RankingsTable
        rankings={{
          ...rankings,
          rankings: [
            makeRanking({ rank: 1, team_key: 'frc254' }),
            makeRanking({ rank: 2, team_key: 'frc33' }),
            makeRanking({ rank: 3, team_key: 'frc1114' }),
          ],
        }}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Team' }));

    const teams = bodyRows().map(
      (row) => within(row).getAllByRole('cell')[1].textContent,
    );
    expect(teams).toEqual(['33', '254', '1114']);
  });

  test('sorts by record using ranking points, keeping null records in place', () => {
    render(
      <RankingsTable
        rankings={{
          ...rankings,
          rankings: [
            makeRanking({ rank: 1, record: { wins: 2, losses: 8, ties: 0 } }),
            makeRanking({ rank: 2, record: { wins: 5, losses: 4, ties: 1 } }),
            makeRanking({ rank: 3, record: null }),
          ],
        }}
        winners={[]}
        captains={[]}
        year={2026}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Record (W-L-T)' }));

    const firstCells = bodyRows().map(
      (row) => within(row).getAllByRole('cell')[0].textContent,
    );
    expect(firstCells[0]).toBe('2');
    expect(firstCells[1]).toBe('1');
  });
});
