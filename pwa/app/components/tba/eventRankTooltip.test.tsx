import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { delay } from 'msw';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { type EventRanking } from '~/api/tba/read';
import { getEventRankings } from '~/api/tba/read/sdk.gen';
import EventRankTooltip from '~/components/tba/eventRankTooltip';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderWithClient } from '~/test/render';

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({
    children,
    teamOrKey,
    year,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    children: ReactNode;
    teamOrKey: string;
    year: number;
  }) => (
    <a href={`/team/${teamOrKey.substring(3)}/${year}`} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/components/ui/tooltip', () => ({
  Tooltip: ({
    children,
    onOpenChange,
  }: {
    children: ReactNode;
    onOpenChange?: (open: boolean) => void;
  }) => (
    <div data-testid="tooltip" onMouseEnter={() => onOpenChange?.(true)}>
      {children}
    </div>
  ),
  TooltipTrigger: ({ children, ...props }: { children: ReactNode }) => (
    <button {...props}>{children}</button>
  ),
  TooltipContent: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
}));

function makeRankings(): EventRanking {
  return {
    rankings: Array.from({ length: 9 }, (_, index) => {
      const rank = 9 - index;
      return {
        rank,
        team_key: `frc${100 + rank}`,
        record: { wins: 10 - rank, losses: rank - 1, ties: 0 },
        matches_played: 9,
        dq: 0,
        qual_average: null,
        sort_orders: [rank / 3],
        extra_stats: [],
      };
    }),
    sort_order_info: [{ name: 'Ranking Score', precision: 2 }],
    extra_stats_info: [],
  };
}

const RANKINGS_PATH = { path: { event_key: '2026miket' } };

function mockRankings(rankings: EventRanking) {
  mockTbaApi(getEventRankings, RANKINGS_PATH, rankings);
}

function holdRankings() {
  const requests: Request[] = [];
  mockTbaApiWith(getEventRankings, RANKINGS_PATH, async ({ request }) => {
    requests.push(request);
    await delay('infinite');
  });
  return requests;
}

function renderTooltip() {
  return renderWithClient(
    <EventRankTooltip
      eventKey="2026miket"
      teamKey="frc103"
      rank={3}
      numTeams={40}
    />,
  );
}

describe('EventRankTooltip', () => {
  test('does not fetch rankings before the tooltip opens', () => {
    const requests = holdRankings();
    renderTooltip();

    expect(requests).toEqual([]);
  });

  test('shows a loading indicator while rankings are pending', async () => {
    const requests = holdRankings();
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    await waitFor(() => expect(requests).toHaveLength(1));
    expect(screen.getByRole('status', { name: 'Loading' })).toBeTruthy();
  });

  test('fetches rankings when the rank is tapped', async () => {
    const requests = holdRankings();
    renderTooltip();

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Rank 3 of 40; show event rankings',
      }),
    );

    await waitFor(() => expect(requests).toHaveLength(1));
  });

  test('shows all rankings in rank order', async () => {
    mockRankings(makeRankings());
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    const table = await screen.findByRole('table');
    expect(
      within(table)
        .getAllByRole('row')
        .slice(1)
        .map((row) => row.textContent),
    ).toEqual([
      '11019-0-03',
      '21028-1-06',
      '31037-2-09',
      '41046-3-012',
      '51055-4-015',
      '61064-5-018',
      '71073-6-021',
      '81082-7-024',
      '91091-8-027',
    ]);
  });

  test('shows total ranking points', async () => {
    mockRankings(makeRankings());
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    expect(
      await screen.findByRole('columnheader', { name: 'RP' }),
    ).toBeTruthy();
  });

  test('marks the current team ranking', async () => {
    mockRankings(makeRankings());
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    expect(
      (await screen.findByRole('row', { name: '3 103 7-2-0 9' })).getAttribute(
        'aria-current',
      ),
    ).toBe('true');
  });

  test('links ranking entries to team season pages', async () => {
    mockRankings(makeRankings());
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    expect(
      (await screen.findByRole('link', { name: '101' })).getAttribute('href'),
    ).toBe('/team/101/2026');
  });

  test('uses whole-number ranking scores as total ranking points', async () => {
    const rankings = makeRankings();
    rankings.sort_order_info = [{ name: 'Ranking Score', precision: 0 }];
    rankings.rankings = rankings.rankings.map((r) => ({
      ...r,
      sort_orders: [r.rank * 2.4],
    }));
    mockRankings(rankings);
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    expect(
      await screen.findByRole('row', { name: '3 103 7-2-0 7' }),
    ).toBeTruthy();
  });

  test('shows a dash for teams without a ranking score', async () => {
    const rankings = makeRankings();
    rankings.rankings = rankings.rankings.map((r) =>
      r.rank === 3 ? { ...r, sort_orders: [] } : r,
    );
    mockRankings(rankings);
    renderTooltip();

    fireEvent.mouseEnter(screen.getByTestId('tooltip'));

    expect(
      await screen.findByRole('row', { name: '3 103 7-2-0 —' }),
    ).toBeTruthy();
  });
});
