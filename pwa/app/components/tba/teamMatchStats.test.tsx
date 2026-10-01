import { fireEvent, render, screen, within } from '@testing-library/react';
import { type ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Event,
  type Match,
  type MatchScoreBreakdown2025,
} from '~/api/tba/read';
import TeamMatchStats from '~/components/tba/teamMatchStats';

vi.mock('~/components/tba/links', () => ({
  TeamLink: ({
    children,
    teamOrKey,
    year,
  }: {
    children: ReactNode;
    teamOrKey: string;
    year?: number;
  }) => (
    <a href={`/team/${teamOrKey.substring(3)}/${year ?? ''}`}>{children}</a>
  ),
}));

vi.mock('recharts', async (importOriginal) => ({
  ...(await importOriginal<typeof import('recharts')>()),
  ResponsiveContainer: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
}));

const TEAM = 'frc254';

function makeMatch({
  eventKey,
  compLevel,
  setNumber = 1,
  matchNumber,
  red,
  blue,
  redScore,
  blueScore,
  scoreBreakdown = null,
}: {
  eventKey: string;
  compLevel: CompLevel;
  setNumber?: number;
  matchNumber: number;
  red: string[];
  blue: string[];
  redScore: number;
  blueScore: number;
  scoreBreakdown?: MatchScoreBreakdown2025 | null;
}): Match {
  const winning_alliance =
    redScore > blueScore
      ? AllianceColor.RED
      : blueScore > redScore
        ? AllianceColor.BLUE
        : AllianceColor.NO_ALLIANCE;
  const suffix =
    compLevel === CompLevel.QM
      ? `qm${matchNumber}`
      : `${compLevel}${setNumber}m${matchNumber}`;
  return {
    key: `${eventKey}_${suffix}`,
    comp_level: compLevel,
    set_number: setNumber,
    match_number: matchNumber,
    alliances: {
      red: {
        score: redScore,
        team_keys: red,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: blueScore,
        team_keys: blue,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance,
    event_key: eventKey,
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: scoreBreakdown,
    videos: [],
  };
}

const partners = [TEAM, 'frc1', 'frc2'];
const partnersB = [TEAM, 'frc1', 'frc6'];
const opponentsA = ['frc3', 'frc4', 'frc5'];
const opponentsB = ['frc3', 'frc7', 'frc8'];

// In order: W, W, T, L (red-carded playoff), unplayed, W, L.
const matches: Match[] = [
  makeMatch({
    eventKey: '2024casj',
    compLevel: CompLevel.QM,
    matchNumber: 1,
    red: partners,
    blue: opponentsA,
    redScore: 50,
    blueScore: 40,
  }),
  makeMatch({
    eventKey: '2024casj',
    compLevel: CompLevel.QM,
    matchNumber: 2,
    red: opponentsB,
    blue: partnersB,
    redScore: 30,
    blueScore: 45,
  }),
  makeMatch({
    eventKey: '2024casj',
    compLevel: CompLevel.QM,
    matchNumber: 3,
    red: partners,
    blue: opponentsA,
    redScore: 20,
    blueScore: 20,
  }),
  // Red card zeroed a winning 80-point score.
  makeMatch({
    eventKey: '2024casj',
    compLevel: CompLevel.SF,
    matchNumber: 1,
    red: partners,
    blue: ['frc9', 'frc10', 'frc11'],
    redScore: 0,
    blueScore: 60,
    scoreBreakdown: {
      red: { adjustPoints: -80 },
      blue: { adjustPoints: 0 },
    } as MatchScoreBreakdown2025,
  }),
  makeMatch({
    eventKey: '2024casj',
    compLevel: CompLevel.SF,
    matchNumber: 2,
    red: partners,
    blue: ['frc9', 'frc10', 'frc11'],
    redScore: -1,
    blueScore: -1,
  }),
  makeMatch({
    eventKey: '2025casj',
    compLevel: CompLevel.QM,
    matchNumber: 1,
    red: partners,
    blue: opponentsA,
    redScore: 100,
    blueScore: 90,
  }),
  makeMatch({
    eventKey: '2025casj',
    compLevel: CompLevel.QM,
    matchNumber: 2,
    red: opponentsB,
    blue: partnersB,
    redScore: 80,
    blueScore: 70,
  }),
];

const events = [{ key: '2024casj' }, { key: '2025casj' }] as Event[];

function statCard(subtitle: string): HTMLElement {
  const dt = screen.getByText(subtitle, { exact: false }).closest('dt');
  const card = dt?.parentElement;
  if (!card) throw new Error(`no card for ${subtitle}`);
  return card;
}

function clickTab(name: string) {
  fireEvent.click(screen.getByRole('tab', { name }));
}

function tableTitled(title: string): HTMLElement {
  const table = screen.getByText(title).closest('.rounded-lg');
  if (!(table instanceof HTMLElement)) throw new Error(`no table ${title}`);
  return table;
}

function firstRowCells(title: string): string[] {
  const rows = within(tableTitled(title)).getAllByRole('row');
  return within(rows[1])
    .getAllByRole('cell')
    .map((c) => c.textContent ?? '');
}

describe('TeamMatchStats', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'ResizeObserver',
      class {
        observe() {}
        unobserve() {}
        disconnect() {}
      },
    );
  });

  test('summarises records, events, matches and teams seen', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    expect(statCard('Qual Winrate').textContent).toContain('60.0%');
    expect(statCard('Qual Winrate').textContent).toContain('3-1-1');
    expect(statCard('Playoff Winrate').textContent).toContain('0.0%');
    expect(statCard('Playoff Winrate').textContent).toContain('0-1-0');
    expect(statCard('Overall Winrate').textContent).toContain('50.0%');
    expect(statCard('Overall Winrate').textContent).toContain('3-2-1');
    expect(statCard('Total Events').textContent).toContain('2');
    expect(statCard('Total Matches').textContent).toContain('7');
    expect(statCard('Unique Teams Seen').textContent).toContain('11');
  });

  test('reports the current and longest streaks', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    const current = statCard('Current Loss Streak');
    expect(current.textContent).toContain('1');
    expect(current.textContent).toContain('2025casj_qm2 → 2025casj_qm2');

    const win = statCard('Longest Win Streak');
    expect(win.textContent).toContain('2');
    expect(win.textContent).toContain('2024casj_qm1 → 2024casj_qm2');

    const loss = statCard('Longest Loss Streak');
    expect(loss.textContent).toContain('1');
    expect(loss.textContent).toContain('2024casj_sf1m1 → 2024casj_sf1m1');
  });

  test('handles a team with no results at all', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={[]} events={[]} />);

    expect(statCard('Qual Winrate').textContent).toContain('0.0%');
    expect(statCard('Current Tie Streak').textContent).toContain('0');
    expect(statCard('Longest Win Streak').textContent).toContain('0');
    expect(screen.getByText('Net Wins Over Time')).toBeTruthy();
  });

  test('lists the high score per year, newest first, highlighting the team alliance', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    const table = tableTitled('High Scores by Year');
    const rows = within(table).getAllByRole('row').slice(1);
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain('2025');
    expect(rows[0].textContent).toContain('2025casj_qm1');
    expect(rows[1].textContent).toContain('2024casj_qm1');

    // 254 was on red in 2025 qm1: red score and red teams are emphasised.
    const cells = within(rows[0]).getAllByRole('cell');
    const [redScore, blueScore] = Array.from(cells[1].querySelectorAll('span'));
    expect(redScore.textContent).toBe('100');
    expect(redScore.className).toContain('font-semibold');
    expect(blueScore.className).toContain('text-muted-foreground');
    const links = within(cells[2]).getAllByRole('link');
    expect(links.map((l) => l.textContent)).toEqual([
      '254',
      '1',
      '2',
      '3',
      '4',
      '5',
    ]);
    expect(links[0].getAttribute('href')).toBe('/team/254/2025');
    expect(links[0].querySelector('span')?.className).toContain(
      'font-semibold',
    );
    expect(links[1].querySelector('span')?.className).not.toContain(
      'font-semibold',
    );
  });

  test('emphasises the blue alliance when the team played blue', () => {
    render(
      <TeamMatchStats teamKey={TEAM} matches={[matches[1]]} events={events} />,
    );

    const rows = within(tableTitled('High Scores by Year')).getAllByRole('row');
    const cells = within(rows[1]).getAllByRole('cell');
    const [redScore, blueScore] = Array.from(cells[1].querySelectorAll('span'));
    expect(redScore.className).toContain('text-muted-foreground');
    expect(blueScore.className).toContain('font-semibold');
    const [redTeams, blueTeams] = Array.from(
      cells[2].querySelector('div')?.children ?? [],
    );
    expect(redTeams.className).toContain('text-muted-foreground');
    expect(blueTeams.className).not.toContain('text-muted-foreground');
  });

  test('uses pre-penalty playoff scores for margins until the checkbox is cleared', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    clickTab('Biggest Wins');
    // With the red card undone, the 80-60 playoff is the biggest 2024 win.
    let rows = within(tableTitled('Biggest Win Margins by Year')).getAllByRole(
      'row',
    );
    expect(rows[2].textContent).toContain('2024casj_sf1m1');

    clickTab('Biggest Losses');
    rows = within(tableTitled('Biggest Loss Margins by Year')).getAllByRole(
      'row',
    );
    // 2025 qm2 (70-80) is the only 2025 loss; 2024 qm3's tie beats the +20 playoff.
    expect(rows[1].textContent).toContain('2025casj_qm2');
    expect(rows[2].textContent).toContain('2024casj_qm3');

    fireEvent.click(screen.getByRole('checkbox'));

    rows = within(tableTitled('Biggest Loss Margins by Year')).getAllByRole(
      'row',
    );
    expect(rows[2].textContent).toContain('2024casj_sf1m1');

    clickTab('Biggest Wins');
    rows = within(tableTitled('Biggest Win Margins by Year')).getAllByRole(
      'row',
    );
    expect(rows[2].textContent).toContain('2024casj_qm2');

    // Re-checking restores the original-score view.
    fireEvent.click(screen.getByRole('checkbox'));
    rows = within(tableTitled('Biggest Win Margins by Year')).getAllByRole(
      'row',
    );
    expect(rows[2].textContent).toContain('2024casj_sf1m1');
  });

  test('ranks partners by matches, wins, losses and record', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    // frc1 partnered in all 7 matches: 3W 2L 1T (one unplayed).
    expect(firstRowCells('Most Played With')).toEqual(['1', '3-2-1', '7']);

    clickTab('Most Wins');
    expect(firstRowCells('Most Wins With')).toEqual(['1', '3-2-1', '3']);

    clickTab('Most Losses');
    expect(firstRowCells('Most Losses With')).toEqual(['1', '3-2-1', '2']);

    clickTab('Best Record');
    const best = firstRowCells('Best Record With');
    expect(best[0]).toBe('1');
    expect(Number(best[2])).toBeGreaterThan(0);

    clickTab('Worst Record');
    const worst = firstRowCells('Worst Record With');
    expect(worst[0]).toBe('1');
    expect(Number(worst[2])).toBeGreaterThan(0);
  });

  test('ranks opponents by matches, wins, losses and record', () => {
    render(<TeamMatchStats teamKey={TEAM} matches={matches} events={events} />);

    clickTab('Against');
    // frc3 opposed in 5 matches: 3W 1L 1T.
    expect(firstRowCells('Most Played Against')).toEqual(['3', '3-1-1', '5']);

    // The inactive "With" panel is unmounted, so these tabs are unique.
    clickTab('Most Wins');
    expect(firstRowCells('Most Wins Against')).toEqual(['3', '3-1-1', '3']);

    clickTab('Most Losses');
    // frc1 partnered 254 in every match, so also "opposed" nobody; frc9-11
    // handed out the only playoff loss but frc3 sorts first on ties.
    expect(firstRowCells('Most Losses Against')[2]).toBe('1');

    clickTab('Best Record');
    // frc4's 2-0-1 has a higher Wilson lower bound than frc3's 3-1-1.
    expect(firstRowCells('Best Record Against')).toEqual([
      '4',
      '2-0-1',
      '0.18',
    ]);

    clickTab('Worst Record');
    // frc9-11 only ever beat 254.
    expect(firstRowCells('Worst Record Against')).toEqual([
      '9',
      '0-1-0',
      '0.10',
    ]);
  });

  test('caps partner tables at their limits', () => {
    // 30 distinct partners, one per match, each a win.
    const many = Array.from({ length: 30 }, (_, i) =>
      makeMatch({
        eventKey: '2025casj',
        compLevel: CompLevel.QM,
        matchNumber: i + 1,
        red: [TEAM, `frc${1000 + i}`, `frc${2000 + i}`],
        blue: [`frc${3000 + i}`, 'frc4', 'frc5'],
        redScore: 10,
        blueScore: 0,
      }),
    );

    render(<TeamMatchStats teamKey={TEAM} matches={many} events={events} />);

    expect(
      within(tableTitled('Most Played With')).getAllByRole('row'),
    ).toHaveLength(26);
    clickTab('Most Wins');
    expect(
      within(tableTitled('Most Wins With')).getAllByRole('row'),
    ).toHaveLength(21);
  });
});
