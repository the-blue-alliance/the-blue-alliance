import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { type EventColors } from '~/api/colors';
import {
  AllianceColor,
  CompLevel,
  type Event,
  type EventRanking,
  EventType,
  type Match,
} from '~/api/tba/read';
import { DistrictChampsTab } from '~/components/tba/districtChampsTab';

const { districtTeamsFn, eventsFn, matchesFn, rankingsFn, colorsFn } =
  vi.hoisted(() => ({
    districtTeamsFn: vi.fn<(districtKey: string) => Promise<string[]>>(),
    eventsFn: vi.fn<(year: number) => Promise<Event[]>>(),
    matchesFn: vi.fn<(eventKey: string) => Promise<Match[]>>(),
    rankingsFn: vi.fn<(eventKey: string) => Promise<EventRanking | null>>(),
    colorsFn: vi.fn<(eventKey: string) => Promise<EventColors>>(),
  }));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getDistrictTeamsKeysOptions: ({
    path,
  }: {
    path: { district_key: string };
  }) => ({
    queryKey: ['district-teams', path.district_key],
    queryFn: () => districtTeamsFn(path.district_key),
  }),
  getEventsByYearOptions: ({ path }: { path: { year: number } }) => ({
    queryKey: ['events', path.year],
    queryFn: () => eventsFn(path.year),
  }),
  getEventMatchesOptions: ({ path }: { path: { event_key: string } }) => ({
    queryKey: ['matches', path.event_key],
    queryFn: () => matchesFn(path.event_key),
  }),
  getEventRankingsOptions: ({ path }: { path: { event_key: string } }) => ({
    queryKey: ['rankings', path.event_key],
    queryFn: () => rankingsFn(path.event_key),
  }),
}));

vi.mock('~/api/colors/@tanstack/react-query.gen', () => ({
  getEventColorsOptions: ({ path }: { path: { eventKey: string } }) => ({
    queryKey: ['colors', path.eventKey],
    queryFn: () => colorsFn(path.eventKey),
  }),
}));

vi.mock('~/components/tba/links', () => ({
  EventLink: ({
    children,
    eventOrKey,
  }: {
    children: ReactNode;
    eventOrKey: string;
  }) => <a href={`/event/${eventOrKey}`}>{children}</a>,
  MatchLink: ({
    children,
    matchOrKey,
  }: {
    children: ReactNode;
    matchOrKey: Match;
  }) => <a href={`/match/${matchOrKey.key}`}>{children}</a>,
  TeamLink: ({
    children,
    teamOrKey,
    style,
  }: {
    children: ReactNode;
    teamOrKey: string;
    style?: React.CSSProperties;
  }) => (
    <a href={`/team/${teamOrKey.substring(3)}`} style={style}>
      {children}
    </a>
  ),
}));

function makeEvent(
  key: string,
  name: string,
  short_name: string | null,
  event_type = EventType.CMP_DIVISION,
): Event {
  return {
    key,
    name,
    short_name,
    event_type,
    event_code: key.substring(4),
    district: null,
    city: null,
    state_prov: null,
    country: null,
    start_date: '2026-04-15',
    end_date: '2026-04-18',
    year: 2026,
    event_type_string: 'Championship Division',
    week: null,
    address: null,
    postal_code: null,
    gmaps_place_id: null,
    gmaps_url: null,
    lat: null,
    lng: null,
    location_name: null,
    timezone: 'America/Chicago',
    website: null,
    first_event_id: null,
    first_event_code: null,
    webcasts: [],
    division_keys: [],
    parent_event_key: '2026cmptx',
    playoff_type: null,
    playoff_type_string: null,
    remap_teams: null,
  };
}

function makeMatch(
  eventKey: string,
  compLevel: CompLevel,
  setNumber: number,
  matchNumber: number,
  red: string[],
  blue: string[],
  redScore: number,
  blueScore: number,
): Match {
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
    score_breakdown: null,
    videos: [],
  };
}

function makeRanking(
  team_key: string,
  rank: number,
  record: EventRanking['rankings'][number]['record'],
): EventRanking['rankings'][number] {
  return {
    team_key,
    rank,
    record,
    matches_played: 10,
    dq: 0,
    qual_average: null,
    sort_orders: [],
    extra_stats: [],
  };
}

const archimedes = makeEvent('2026arc', 'Archimedes Division', 'Archimedes');
const newton = makeEvent('2026new', 'Newton Division', null);
const regional = makeEvent(
  '2026casj',
  'Silicon Valley Regional',
  'SVR',
  EventType.REGIONAL,
);

const DISTRICT_TEAMS = ['frc1', 'frc2', 'frc3', 'frc4', 'frc5'];

const archimedesMatches: Match[] = [
  // Given out of order to prove sorting; sf before qm.
  makeMatch(
    '2026arc',
    CompLevel.SF,
    1,
    1,
    ['frc2', 'frc10'],
    ['frc1', 'frc11'],
    -1,
    -1,
  ),
  makeMatch(
    '2026arc',
    CompLevel.QM,
    1,
    1,
    ['frc1', 'frc10', 'frc11'],
    ['frc20', 'frc21', 'frc22'],
    50,
    40,
  ),
  // No district teams: filtered out entirely.
  makeMatch(
    '2026arc',
    CompLevel.QM,
    1,
    2,
    ['frc30', 'frc31', 'frc32'],
    ['frc20', 'frc21', 'frc22'],
    50,
    40,
  ),
  makeMatch(
    '2026arc',
    CompLevel.QM,
    1,
    3,
    ['frc4', 'frc5', 'frc12'],
    ['frc2', 'frc21', 'frc22'],
    10,
    30,
  ),
];

const newtonMatches: Match[] = [
  makeMatch(
    '2026new',
    CompLevel.QM,
    1,
    1,
    ['frc40', 'frc41', 'frc42'],
    ['frc3', 'frc43', 'frc44'],
    20,
    25,
  ),
];

const archimedesRankings: EventRanking = {
  rankings: [
    makeRanking('frc1', 1, { wins: 8, losses: 2, ties: 0 }),
    makeRanking('frc10', 2, { wins: 7, losses: 3, ties: 0 }),
    makeRanking('frc2', 3, null),
  ],
  sort_order_info: [],
  extra_stats_info: [],
};

const newtonRankings: EventRanking = {
  rankings: [makeRanking('frc3', 1, { wins: 9, losses: 1, ties: 0 })],
  sort_order_info: [],
  extra_stats_info: [],
};

const archimedesColors: EventColors = {
  teams: {
    // Verified: dark background, white text, secondary outline.
    '1': {
      teamNumber: 1,
      colors: { primaryHex: '0000ff', secondaryHex: 'ffcc00', verified: true },
    },
    // Unverified: light background, black text, no outline.
    '2': {
      teamNumber: 2,
      colors: { primaryHex: '#ffffff', secondaryHex: '#000', verified: false },
    },
    // Short hex cannot be parsed: white text.
    '4': {
      teamNumber: 4,
      colors: { primaryHex: '#fff', secondaryHex: '#000', verified: false },
    },
    // Non-hex characters: white text.
    '5': {
      teamNumber: 5,
      colors: { primaryHex: '#zzzzzz', secondaryHex: '#000', verified: false },
    },
    '10': { teamNumber: 10, colors: null },
  },
};

function setupQueries({
  events = [archimedes, newton, regional],
  teams = DISTRICT_TEAMS,
  rankings = {
    '2026arc': archimedesRankings,
    '2026new': newtonRankings,
  } as Record<string, EventRanking | null>,
  matches = {
    '2026arc': archimedesMatches,
    '2026new': newtonMatches,
  } as Record<string, Match[]>,
}: {
  events?: Event[];
  teams?: string[];
  rankings?: Record<string, EventRanking | null>;
  matches?: Record<string, Match[]>;
} = {}) {
  districtTeamsFn.mockResolvedValue(teams);
  eventsFn.mockResolvedValue(events);
  matchesFn.mockImplementation((key) => Promise.resolve(matches[key] ?? []));
  rankingsFn.mockImplementation((key) =>
    Promise.resolve(rankings[key] ?? null),
  );
  colorsFn.mockImplementation((key) =>
    key === '2026arc'
      ? Promise.resolve(archimedesColors)
      : // Never resolves: exercises the "no colours yet" path.
        new Promise(() => {}),
  );
}

function renderTab(
  props: Partial<Parameters<typeof DistrictChampsTab>[0]> = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <DistrictChampsTab
        abbreviation="fim"
        currentSeason={2026}
        year={2025}
        {...props}
      />
    </QueryClientProvider>,
  );
}

function clickTab(name: string) {
  fireEvent.click(screen.getByRole('tab', { name }));
}

async function waitForDivisions() {
  await waitFor(() =>
    expect(screen.getByRole('tab', { name: 'Archimedes' })).toBeTruthy(),
  );
  await waitFor(() =>
    expect(screen.queryByText('Loading divisions…')).toBeNull(),
  );
}

describe('DistrictChampsTab', () => {
  beforeEach(() => {
    setupQueries();
  });

  test('shows a loading state, then tabs for each championship division', async () => {
    renderTab();

    expect(screen.getByText('Loading divisions…')).toBeTruthy();
    expect(districtTeamsFn).toHaveBeenCalledWith('2025fim');
    expect(eventsFn).toHaveBeenCalledWith(2025);

    await waitForDivisions();
    const tabs = screen.getAllByRole('tab').map((t) => t.textContent);
    expect(tabs).toEqual([
      'Rankings',
      'Archimedes',
      'Newton Division',
      'All Matches',
    ]);
    // No auto-refresh badge for a past season.
    expect(screen.queryByText(/Auto-refresh/)).toBeNull();
  });

  test('explains when the year has no divisions', async () => {
    setupQueries({ events: [regional] });
    renderTab();

    await waitFor(() =>
      expect(
        screen.getByText('No FIRST Championship divisions found for 2025.'),
      ).toBeTruthy(),
    );
    expect(screen.getByText('No rankings available yet.')).toBeTruthy();
  });

  test('merges district-team rankings across divisions, ordered by rank then division', async () => {
    renderTab();
    await waitForDivisions();

    await waitFor(() =>
      expect(screen.getByRole('link', { name: '3' })).toBeTruthy(),
    );
    const rows = screen.getAllByRole('row').slice(1);
    const cells = rows.map((row) =>
      within(row)
        .getAllByRole('cell')
        .map((c) => c.textContent),
    );
    expect(cells).toEqual([
      ['1', '1', 'Archimedes', '8-2-0', '10'],
      ['1', '3', 'Newton Division', '9-1-0', '10'],
      ['3', '2', 'Archimedes', '0-0-0', '10'],
    ]);
    expect(
      screen
        .getAllByRole('link', { name: 'Archimedes' })[0]
        .getAttribute('href'),
    ).toBe('/event/2026arc');
  });

  test('lists a division rankings and matches, colouring district teams', async () => {
    renderTab();
    await waitForDivisions();
    await waitFor(() =>
      expect(screen.getByRole('link', { name: '3' })).toBeTruthy(),
    );

    clickTab('Archimedes');
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Matches' })).toBeTruthy(),
    );

    // Rankings: district teams only, with a dash for a missing record.
    const rankingsCard = screen
      .getByRole('heading', { name: /^Rankings/ })
      .closest('.rounded-xl') as HTMLElement;
    expect(
      within(rankingsCard)
        .getByRole('link', { name: 'Archimedes' })
        .getAttribute('href'),
    ).toBe('/event/2026arc');
    const rankingRows = within(rankingsCard).getAllByRole('row').slice(1);
    expect(rankingRows.map((r) => r.textContent)).toEqual([
      '118-2-010',
      '32—10',
    ]);

    // Matches: sorted, filtered to district teams, played and unplayed.
    const matchesCard = screen
      .getByRole('heading', { name: 'Matches' })
      .closest('.rounded-xl') as HTMLElement;
    const desktop = matchesCard.querySelector(
      '.hidden.md\\:block',
    ) as HTMLElement;
    const matchRows = within(desktop).getAllByRole('row').slice(1);
    expect(
      matchRows.map((r) => within(r).getAllByRole('cell')[0].textContent),
    ).toEqual(['qm1', 'qm3', 'sf1-1']);
    expect(
      within(matchRows[0])
        .getByRole('link', { name: 'qm1' })
        .getAttribute('href'),
    ).toBe('/match/2026arc_qm1');
    // Played scores, with the winner tinted.
    const qm1Cells = within(matchRows[0]).getAllByRole('cell');
    expect(qm1Cells[4].textContent).toBe('50');
    expect(qm1Cells[4].className).toContain('alliance-red-accent');
    expect(qm1Cells[5].textContent).toBe('40');
    expect(qm1Cells[5].className).toContain('bg-alliance-blue-loser');
    const qm3Cells = within(matchRows[1]).getAllByRole('cell');
    expect(qm3Cells[5].className).toContain('alliance-blue-accent');
    // Unplayed: dashes and padding cells for two-team alliances.
    const sfCells = within(matchRows[2]).getAllByRole('cell');
    expect(sfCells).toHaveLength(9);
    expect(sfCells[4].textContent).toBe('—');
    expect(sfCells[5].textContent).toBe('—');

    // Team colours: verified dark primary gets white text and an outline.
    const team1 = within(matchRows[0])
      .getByRole('link', { name: '1' })
      .closest('td');
    expect(team1?.style.backgroundColor).toBe('rgb(0, 0, 255)');
    expect(team1?.style.color).toBe('white');
    expect(team1?.style.outline).toBe('2px solid #ffcc00');
    expect(team1?.querySelector('div')?.className).toBe('font-bold');
    // Unverified light primary: black text, no outline.
    const team2 = within(matchRows[1])
      .getByRole('link', { name: '2' })
      .closest('td');
    expect(team2?.style.backgroundColor).toBe('rgb(255, 255, 255)');
    expect(team2?.style.color).toBe('black');
    expect(team2?.style.outline).toBe('');
    // Unparseable hex values fall back to white text.
    const team4 = within(matchRows[1])
      .getByRole('link', { name: '4' })
      .closest('td');
    expect(team4?.style.color).toBe('white');
    const team5 = within(matchRows[1])
      .getByRole('link', { name: '5' })
      .closest('td');
    expect(team5?.style.color).toBe('white');
    // Non-district teams keep the alliance background and are dimmed.
    const team10 = within(matchRows[0])
      .getByRole('link', { name: '10' })
      .closest('td');
    expect(team10?.className).toContain('bg-alliance-red-loser');
    expect(team10?.querySelector('div')?.className).toBe('opacity-70');

    // The mobile layout renders the same matches two rows at a time.
    const mobile = matchesCard.querySelector('.md\\:hidden') as HTMLElement;
    expect(within(mobile).getAllByRole('row')).toHaveLength(7);
  });

  test('shows empty states for a division without rankings or matches', async () => {
    setupQueries({
      rankings: { '2026arc': archimedesRankings, '2026new': null },
      matches: { '2026arc': archimedesMatches, '2026new': [] },
    });
    renderTab();
    await waitForDivisions();

    clickTab('Newton Division');
    await waitFor(() =>
      expect(screen.getByText('No rankings available.')).toBeTruthy(),
    );
    expect(screen.getByText('No matches yet.')).toBeTruthy();
  });

  test('says when no district teams are ranked yet', async () => {
    setupQueries({
      rankings: {
        '2026arc': archimedesRankings,
        '2026new': {
          rankings: [makeRanking('frc99', 1, null)],
          sort_order_info: [],
          extra_stats_info: [],
        },
      },
    });
    renderTab();
    await waitForDivisions();

    clickTab('Newton Division');
    await waitFor(() =>
      expect(
        screen.getByText('No district teams in rankings yet.'),
      ).toBeTruthy(),
    );
  });

  test('combines every division on the all-matches tab with a division column', async () => {
    renderTab();
    await waitForDivisions();

    clickTab('All Matches');
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'All Matches' })).toBeTruthy(),
    );

    const card = screen
      .getByRole('heading', { name: 'All Matches' })
      .closest('.rounded-xl') as HTMLElement;
    const desktop = card.querySelector('.hidden.md\\:block') as HTMLElement;
    expect(
      within(desktop)
        .getAllByRole('columnheader')
        .map((h) => h.textContent),
    ).toEqual([
      'Match',
      'Division',
      'Red Alliance',
      'Red',
      'Blue',
      'Blue Alliance',
    ]);
    const rows = within(desktop).getAllByRole('row').slice(1);
    expect(
      rows.map((r) =>
        within(r)
          .getAllByRole('cell')
          .slice(0, 2)
          .map((c) => c.textContent),
      ),
    ).toEqual([
      ['qm1', 'Archimedes'],
      ['qm1', 'Newton Division'],
      ['qm3', 'Archimedes'],
      ['sf1-1', 'Archimedes'],
    ]);
    // Newton's colours never loaded, so its district team is plain.
    const team3 = within(rows[1])
      .getByRole('link', { name: '3' })
      .closest('td');
    expect(team3?.style.backgroundColor).toBe('');
    expect(team3?.className).toContain('bg-alliance-blue-loser');

    const mobile = card.querySelector('.md\\:hidden') as HTMLElement;
    expect(
      within(mobile)
        .getAllByRole('columnheader')
        .map((h) => h.textContent),
    ).toEqual(['Match', 'Division', 'Teams', 'Score']);
  });

  describe('live polling', () => {
    beforeEach(() => {
      vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    test('counts down to the next refresh and resets once a fetch completes', async () => {
      const { unmount } = renderTab({ year: 2026 });

      expect(districtTeamsFn).toHaveBeenCalledWith('2026fim');
      expect(screen.getByText('Refreshing…')).toBeTruthy();

      await waitForDivisions();
      await waitFor(() =>
        expect(screen.getByText('Auto-refresh in 60s')).toBeTruthy(),
      );

      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByText('Auto-refresh in 59s')).toBeTruthy();

      act(() => {
        vi.advanceTimersByTime(58_000);
      });
      expect(screen.getByText('Auto-refresh in 1s')).toBeTruthy();

      // The final tick wraps the countdown and React Query's own 60s
      // refetch interval fires, so the badge reports the refresh in
      // progress and then resets once it settles.
      expect(eventsFn).toHaveBeenCalledTimes(1);
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByText('Refreshing…')).toBeTruthy();
      await waitFor(() =>
        expect(screen.getByText('Auto-refresh in 60s')).toBeTruthy(),
      );
      expect(eventsFn).toHaveBeenCalledTimes(2);

      unmount();
      expect(vi.getTimerCount()).toBe(0);
    });
  });
});
