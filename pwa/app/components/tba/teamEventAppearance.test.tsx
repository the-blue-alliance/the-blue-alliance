import { render, screen, within } from '@testing-library/react';
import { type ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  type Award,
  AwardType,
  type EliminationAlliance,
  type Event,
  type EventDistrictPoints,
  EventType,
  type Match,
  type RegionalAdvancement,
  type Team,
  type TeamEventStatus,
} from '~/api/tba/read';
import TeamEventAppearance, {
  TeamStatus,
  getTotalRankingPoints,
} from '~/components/tba/teamEventAppearance';

vi.mock('~/components/tba/links', () => ({
  EventLink: ({
    children,
    eventOrKey,
  }: {
    children: ReactNode;
    eventOrKey: string;
  }) => <a href={`/event/${eventOrKey}`}>{children}</a>,
  EventLocationLink: ({ event }: { event: Event }) => (
    <a href="https://maps.example">{event.city}</a>
  ),
  TeamLink: ({
    children,
    teamOrKey,
    year,
    ...props
  }: {
    children: ReactNode;
    teamOrKey: string;
    year?: number;
    'aria-current'?: 'page';
  }) => (
    <a href={`/team/${teamOrKey.substring(3)}/${year ?? ''}`} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/components/tba/eventRankTooltip', () => ({
  default: ({ rank, numTeams }: { rank: number; numTeams: number }) => (
    <div data-testid="rank">
      {rank} of {numTeams}
    </div>
  ),
}));

vi.mock('~/components/tba/match/matchRows', () => ({
  default: ({
    matches,
    focusTeamKey,
  }: {
    matches: Match[];
    focusTeamKey: string;
  }) => (
    <ul data-testid="matches" data-focus={focusTeamKey}>
      {matches.map((m) => (
        <li key={m.key}>{m.key}</li>
      ))}
    </ul>
  ),
}));

const event = {
  event_type: EventType.REGIONAL,
  key: '2026test',
  year: 2026,
} as Event;

const status = {
  qual: {
    ranking: {
      matches_played: 12,
      rank: null,
      record: { wins: 8, losses: 4, ties: 0 },
      sort_orders: [3],
    },
    sort_order_info: [{ name: 'Ranking Score', precision: 2 }],
  },
} satisfies TeamEventStatus;

describe('getTotalRankingPoints', () => {
  test('converts an average ranking score to total ranking points', () => {
    expect(getTotalRankingPoints(event, status)).toBe(36);
  });

  test('preserves a ranking score that is already a total', () => {
    const totalStatus = {
      qual: {
        ranking: { matches_played: 12, sort_orders: [39] },
        sort_order_info: [{ name: 'Ranking Score', precision: 0 }],
      },
    } satisfies TeamEventStatus;

    expect(getTotalRankingPoints(event, totalStatus)).toBe(39);
  });

  test('omits ranking points when ranking score metadata is unavailable', () => {
    const statusWithoutRankingScore = {
      qual: {
        ranking: { matches_played: 12, sort_orders: [3] },
        sort_order_info: [],
      },
    } satisfies TeamEventStatus;

    expect(
      getTotalRankingPoints(event, statusWithoutRankingScore),
    ).toBeUndefined();
  });

  test('omits ranking points before 2016 and without a status', () => {
    expect(
      getTotalRankingPoints({ ...event, year: 2015 }, status),
    ).toBeUndefined();
    expect(getTotalRankingPoints(event, null)).toBeUndefined();
  });

  test('omits ranking points when matches played is unknown', () => {
    const noMatchesPlayed = {
      qual: {
        ranking: { sort_orders: [3] },
        sort_order_info: [{ name: 'Ranking Score', precision: 2 }],
      },
    } as TeamEventStatus;

    expect(getTotalRankingPoints(event, noMatchesPlayed)).toBeUndefined();
  });
});

describe('TeamStatus', () => {
  test('shows total ranking points below the team record', () => {
    render(
      <TeamStatus
        event={event}
        matches={[makeMatch('2026test_qm1', 'qm', 1, ['frc254'])]}
        status={status}
        team={{ key: 'frc254' } as Team}
        awards={[]}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={null}
      />,
    );

    expect(screen.getByText('36 RP')).toBeTruthy();
  });
});

const team = { key: 'frc254', team_number: 254 } as Team;

const fullEvent: Event = {
  key: '2026casj',
  name: 'Silicon Valley Regional',
  event_code: 'casj',
  event_type: EventType.REGIONAL,
  district: null,
  city: 'San Jose',
  state_prov: 'CA',
  country: 'USA',
  start_date: '2026-03-26',
  end_date: '2026-03-29',
  year: 2026,
  short_name: 'Silicon Valley',
  event_type_string: 'Regional',
  week: 4,
  address: null,
  postal_code: null,
  gmaps_place_id: null,
  gmaps_url: null,
  lat: null,
  lng: null,
  location_name: 'San Jose State',
  timezone: 'America/Los_Angeles',
  website: null,
  first_event_id: null,
  first_event_code: null,
  webcasts: [],
  division_keys: [],
  parent_event_key: null,
  playoff_type: null,
  playoff_type_string: null,
  remap_teams: null,
};

const fullStatus = {
  qual: {
    num_teams: 40,
    status: 'completed',
    ranking: {
      matches_played: 10,
      rank: 3,
      record: { wins: 7, losses: 3, ties: 0 },
      sort_orders: [2.5],
      team_key: 'frc254',
      qual_average: null,
      dq: 0,
    },
    sort_order_info: [{ name: 'Ranking Score', precision: 2 }],
  },
  alliance: {
    name: 'Alliance 1',
    number: 1,
    pick: 0,
    backup: null,
  },
  playoff: {
    level: 'f',
    status: 'won',
    record: { wins: 4, losses: 1, ties: 0 },
    current_level_record: null,
    playoff_average: null,
  },
} as unknown as TeamEventStatus;

const alliances: EliminationAlliance[] = [
  { declines: [], picks: ['frc254', 'frc1678', 'frc971'] },
  { declines: [], picks: ['frc118', 'frc148', 'frc1114'] },
];

const awards: Award[] = [
  {
    name: 'Regional Winners',
    award_type: AwardType.WINNER,
    event_key: '2026casj',
    year: 2026,
    recipient_list: [
      { team_key: 'frc254', awardee: null },
      { team_key: 'frc1678', awardee: null },
    ],
  },
  {
    name: "FIRST Dean's List Finalist",
    award_type: AwardType.DEANS_LIST,
    event_key: '2026casj',
    year: 2026,
    recipient_list: [
      { team_key: 'frc254', awardee: 'Ada Lovelace' },
      { team_key: 'frc254', awardee: 'Grace Hopper' },
      { team_key: 'frc254', awardee: '' },
      { team_key: 'frc1678', awardee: 'Someone Else' },
    ],
  },
];

const points: EventDistrictPoints = {
  points: {
    frc254: {
      qual_points: 20,
      alliance_points: 16,
      elim_points: 30,
      award_points: 5,
      total: 71,
    },
  },
};

function makeMatch(
  key: string,
  compLevel: 'qm' | 'sf',
  matchNumber: number,
  red: string[] = [],
  blue: string[] = [],
) {
  return {
    key,
    comp_level: compLevel,
    set_number: 1,
    match_number: matchNumber,
    event_key: '2026casj',
    winning_alliance: 'red',
    alliances: {
      red: {
        score: 1,
        team_keys: red,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: 0,
        team_keys: blue,
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  } as unknown as Match;
}

describe('TeamEventAppearance', () => {
  test('renders the event header, sorted matches, status and banners', () => {
    const matches = [
      makeMatch('2026casj_sf1m1', 'sf', 1),
      makeMatch('2026casj_qm2', 'qm', 2),
      makeMatch('2026casj_qm1', 'qm', 1),
    ];

    const { container } = render(
      <TeamEventAppearance
        event={fullEvent}
        matches={matches}
        status={fullStatus}
        team={team}
        awards={awards}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={alliances}
      />,
    );

    expect(container.querySelector('[id="2026casj"]')).toBeTruthy();
    expect(
      screen
        .getByRole('link', { name: 'Silicon Valley Regional' })
        .getAttribute('href'),
    ).toBe('/event/2026casj');
    expect(screen.getByText('March 26 to March 29, 2026')).toBeTruthy();
    expect(screen.getByText('Week 5')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'San Jose' })).toBeTruthy();
    expect(screen.getByLabelText('Add to calendar')).toBeTruthy();

    const list = screen.getByTestId('matches');
    expect(list.getAttribute('data-focus')).toBe('frc254');
    expect(
      within(list)
        .getAllByRole('listitem')
        .map((li) => li.textContent),
    ).toEqual(['2026casj_qm1', '2026casj_qm2', '2026casj_sf1m1']);

    // Only the blue-banner award (Winner) becomes a banner.
    expect(screen.getAllByTestId('award-banner')).toHaveLength(1);
    expect(screen.getByTestId('rank').textContent).toBe('3 of 40');
  });

  test('omits the week badge and banners for offseason events', () => {
    render(
      <TeamEventAppearance
        event={{ ...fullEvent, event_type: EventType.OFFSEASON, week: null }}
        matches={[]}
        status={null}
        team={team}
        awards={awards}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={null}
      />,
    );

    expect(screen.queryByText(/Week/)).toBeNull();
    expect(screen.queryByTestId('award-banner')).toBeNull();
  });

  test('omits banners when the team won none', () => {
    render(
      <TeamEventAppearance
        event={fullEvent}
        matches={[]}
        status={null}
        team={team}
        awards={[awards[1]]}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={null}
      />,
    );

    expect(screen.queryByTestId('award-banner')).toBeNull();
  });
});

describe('TeamStatus sections', () => {
  function renderStatus(
    overrides: Partial<Parameters<typeof TeamStatus>[0]> = {},
  ) {
    return render(
      <TeamStatus
        event={fullEvent}
        matches={[
          makeMatch('2026casj_qm1', 'qm', 1, ['frc254']),
          makeMatch('2026casj_qm2', 'qm', 2, [], ['frc254']),
          makeMatch('2026casj_sf1m1', 'sf', 1, ['frc254']),
        ]}
        status={fullStatus}
        team={team}
        awards={awards}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={alliances}
        {...overrides}
      />,
    );
  }

  test('renders nothing when there is nothing to show', () => {
    const { container } = renderStatus({
      matches: [],
      status: null,
      awards: [],
      maybeAlliances: null,
    });
    expect(container.innerHTML).toBe('');
  });

  test('combines qualification and playoff records', () => {
    renderStatus();

    expect(screen.getByText('2-1-0')).toBeTruthy();
    expect(screen.getByText('25 RP')).toBeTruthy();
    expect(screen.getByTestId('rank').textContent).toBe('3 of 40');
  });

  test('shows the record alone when the team is unranked', () => {
    renderStatus({
      status: {
        ...fullStatus,
        qual: {
          ...fullStatus.qual,
          ranking: { ...fullStatus.qual?.ranking, rank: null },
        },
      } as unknown as TeamEventStatus,
    });

    expect(screen.queryByTestId('rank')).toBeNull();
    expect(screen.getByText('2-1-0')).toBeTruthy();
  });

  test('excludes playoff matches the team did not play', () => {
    renderStatus({
      matches: [
        makeMatch('2026casj_qm1', 'qm', 1, ['frc254']),
        makeMatch('2026casj_qm2', 'qm', 2, ['frc254']),
        makeMatch('2026casj_sf1m1', 'sf', 1, ['frc1678', 'frc971']),
      ],
    });

    expect(screen.getByText('2-0-0')).toBeTruthy();
  });

  test('omits the record at 2015 events', () => {
    renderStatus({ event: { ...fullEvent, year: 2015 } });

    expect(screen.queryByText('Record')).toBeNull();
  });

  test('lists the alliance with the team itself marked current', () => {
    renderStatus();

    expect(screen.getByText('Alliance 1')).toBeTruthy();
    const self = screen.getByRole('link', { name: '254' });
    expect(self.getAttribute('aria-current')).toBe('page');
    expect(self.getAttribute('href')).toBe('/team/254/2026');
    expect(
      screen.getByRole('link', { name: '1678' }).getAttribute('aria-current'),
    ).toBeNull();
    expect(screen.queryByRole('link', { name: '118' })).toBeNull();
  });

  test('falls back to a generic alliance heading', () => {
    renderStatus({
      status: {
        ...fullStatus,
        alliance: { number: 1, pick: 0, backup: null },
      } as unknown as TeamEventStatus,
    });

    expect(screen.getByText('Alliance')).toBeTruthy();
  });

  test('hides the alliance section when alliances are unknown', () => {
    renderStatus({ maybeAlliances: [] });

    expect(screen.queryByText('Alliance 1')).toBeNull();
  });

  test('lists awards with the team named recipients', () => {
    renderStatus();

    expect(screen.getByText('Awards')).toBeTruthy();
    const items = screen.getAllByRole('listitem');
    expect(items[0].textContent).toBe('Regional Winners');
    expect(items[1].textContent).toBe(
      "FIRST Dean's List Finalist (Ada Lovelace, Grace Hopper)",
    );
  });

  test('shows district points at district events', () => {
    renderStatus({
      event: { ...fullEvent, event_type: EventType.DISTRICT },
      maybeDistrictPoints: points,
    });

    expect(screen.getByText('District Points')).toBeTruthy();
    expect(screen.getByText('Quals').nextElementSibling?.textContent).toBe(
      '20',
    );
    expect(screen.getByText('Alliance').nextElementSibling?.textContent).toBe(
      '16',
    );
    expect(screen.getByText('Playoff').nextElementSibling?.textContent).toBe(
      '30',
    );
    expect(screen.getByText('Award').nextElementSibling?.textContent).toBe('5');
    expect(screen.getByText('Total').nextElementSibling?.textContent).toBe(
      '71',
    );
  });

  test('ignores district points for teams without any and at non-district events', () => {
    const { unmount } = renderStatus({
      event: { ...fullEvent, event_type: EventType.DISTRICT },
      maybeDistrictPoints: { points: {} },
    });
    expect(screen.queryByText('District Points')).toBeNull();
    unmount();

    renderStatus({ maybeDistrictPoints: points });
    expect(screen.queryByText('District Points')).toBeNull();
  });

  test('shows regional pool points at regionals', () => {
    renderStatus({ maybeRegionalPoolPoints: points });

    expect(screen.getByText('Regional Pool Points')).toBeTruthy();
    expect(screen.queryByText('Qualified')).toBeNull();
    expect(screen.getByText('Total').nextElementSibling?.textContent).toBe(
      '71',
    );
  });

  test('hides regional pool points at district events', () => {
    renderStatus({
      event: { ...fullEvent, event_type: EventType.DISTRICT },
      maybeRegionalPoolPoints: points,
    });

    expect(screen.queryByText('Regional Pool Points')).toBeNull();
  });

  test('marks the event where the team earned its pool invitation', () => {
    const advancement: RegionalAdvancement = {
      cmp: true,
      cmp_status: 'EventQualified',
      qualifying_event: '2026casj',
      qualifying_pool_week: 5,
    };

    renderStatus({
      maybeRegionalPoolPoints: points,
      teamRegionalAdvancement: advancement,
    });

    expect(screen.getByText('Qualified')).toBeTruthy();
  });

  test('marks the week of a pool qualification when no event is recorded', () => {
    const advancement: RegionalAdvancement = {
      cmp: true,
      cmp_status: 'PoolQualified',
      qualifying_pool_week: 5,
    };

    const { unmount } = renderStatus({
      maybeRegionalPoolPoints: points,
      teamRegionalAdvancement: advancement,
    });
    expect(screen.getByText('Qualified')).toBeTruthy();
    unmount();

    // A different week does not qualify.
    const { unmount: unmountOther } = renderStatus({
      event: { ...fullEvent, week: 1 },
      maybeRegionalPoolPoints: points,
      teamRegionalAdvancement: advancement,
    });
    expect(screen.queryByText('Qualified')).toBeNull();
    unmountOther();

    // Nor does an event with no week at all.
    renderStatus({
      event: { ...fullEvent, week: null },
      maybeRegionalPoolPoints: points,
      teamRegionalAdvancement: advancement,
    });
    expect(screen.queryByText('Qualified')).toBeNull();
  });

  test('does not mark qualification earned at another event', () => {
    renderStatus({
      maybeRegionalPoolPoints: points,
      teamRegionalAdvancement: {
        cmp: true,
        cmp_status: 'EventQualified',
        qualifying_event: '2026other',
        qualifying_pool_week: 5,
      },
    });

    expect(screen.queryByText('Qualified')).toBeNull();
  });
});
