import { fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { Temporal } from 'temporal-polyfill';
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Event,
  EventType,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import type { ShouldInsertBreakCallback } from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks, {
  BreakRow,
  MatchRow,
  SimpleMatchRow,
} from '~/components/tba/match/matchRows';
import type { TeamTooltipProps } from '~/components/tba/teamTooltip';
import { TooltipProvider } from '~/components/ui/tooltip';
import { formatMatchTime } from '~/lib/matchUtils';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/components/tba/links', () => ({
  MatchLink: ({
    children,
    matchOrKey,
  }: {
    children: ReactNode;
    matchOrKey: Match;
  }) => <a href={`/match/${matchOrKey.key}`}>{children}</a>,
}));

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({
    teamKey,
    year,
    disqualified: _disqualified,
    surrogate: _surrogate,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & TeamTooltipProps) => (
    <a href={`/team/${teamKey.substring(3)}/${year}`} {...props}>
      {teamKey.substring(3)}
    </a>
  ),
}));

const mocks = vi.hoisted(() => ({
  useFavoriteTeamKeys:
    vi.fn<() => { teamKeys: string[]; isLoading: boolean }>(),
}));

vi.mock('~/lib/hooks/useFavoriteTeams', () => ({
  useFavoriteTeamKeys: mocks.useFavoriteTeamKeys,
}));

beforeEach(() => {
  mocks.useFavoriteTeamKeys.mockReturnValue({ teamKeys: [], isLoading: false });
});

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

afterEach(() => {
  vi.restoreAllMocks();
});

const event: Event = {
  key: '2026test',
  name: 'Test Event',
  event_code: 'test',
  event_type: EventType.REGIONAL,
  district: null,
  city: null,
  state_prov: null,
  country: null,
  start_date: '2026-03-06',
  end_date: '2026-03-08',
  year: 2026,
  short_name: null,
  event_type_string: 'Regional',
  week: 0,
  address: null,
  postal_code: null,
  gmaps_place_id: null,
  gmaps_url: null,
  lat: null,
  lng: null,
  location_name: null,
  timezone: 'America/New_York',
  website: null,
  first_event_id: null,
  first_event_code: null,
  webcasts: [],
  division_keys: [],
  parent_event_key: null,
  playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
  playoff_type_string: null,
  remap_teams: null,
};

function makeMatch(overrides: Partial<Match> = {}): Match {
  return {
    key: '2026test_qm1',
    comp_level: CompLevel.QM,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: {
        score: 94,
        team_keys: ['frc254', 'frc1114', 'frc2056'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: 43,
        team_keys: ['frc148', 'frc217', 'frc33'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance: AllianceColor.RED,
    event_key: '2026test',
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
    ...overrides,
  };
}

function makeUnplayedMatch(overrides: Partial<Match> = {}): Match {
  return makeMatch({
    alliances: {
      red: {
        score: -1,
        team_keys: ['frc254', 'frc1114', 'frc2056'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: -1,
        team_keys: ['frc148', 'frc217', 'frc33'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance: '' as AllianceColor,
    ...overrides,
  });
}

function makeMatches(count: number): Match[] {
  return Array.from({ length: count }, (_, index) =>
    makeMatch({
      key: `2026test_qm${index + 1}`,
      match_number: index + 1,
      videos: [{ type: 'youtube', key: `vid${index + 1}` }],
    }),
  );
}

const breakBeforeFirst: ShouldInsertBreakCallback = ({ matchIndex }) => ({
  shouldBreak: matchIndex === 0,
  text: 'Qualifications',
  whereToInsertBreak: 'before',
});

const breakAfterEach: ShouldInsertBreakCallback = () => ({
  shouldBreak: true,
  text: 'End of Day',
  size: 'small',
  whereToInsertBreak: 'after',
});

const untitledBreakAfterEach: ShouldInsertBreakCallback = () => ({
  shouldBreak: true,
  whereToInsertBreak: 'after',
});

const neverBreak: ShouldInsertBreakCallback = () => ({ shouldBreak: false });

function linkHrefs() {
  return screen.getAllByRole('link').map((link) => link.getAttribute('href'));
}

describe('SimpleMatchRowsWithBreaks', () => {
  test('renders a linked row for every match', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(3)}
        event={event}
        breakers={[neverBreak]}
      />,
    );

    expect(
      [
        screen.getByRole('link', { name: 'Quals 1' }),
        screen.getByRole('link', { name: 'Quals 2' }),
        screen.getByRole('link', { name: 'Quals 3' }),
      ].map((link) => link.getAttribute('href')),
    ).toEqual([
      '/match/2026test_qm1',
      '/match/2026test_qm2',
      '/match/2026test_qm3',
    ]);
  });

  test('inserts a break row before a match when a breaker asks for one', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(2)}
        event={event}
        breakers={[breakBeforeFirst]}
      />,
    );

    expect(screen.getByText('Qualifications')).toBeTruthy();
  });

  test('inserts a break row after each match when a breaker asks for one', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(2)}
        event={event}
        breakers={[breakAfterEach]}
      />,
    );

    expect(screen.getAllByText('End of Day')).toHaveLength(2);
  });

  test('titles a break "Break" when the breaker gives no text', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(1)}
        event={event}
        breakers={[untitledBreakAfterEach]}
      />,
    );

    expect(screen.getByText('Break')).toBeTruthy();
  });

  test('attaches the video playlist to only the first break row', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(2)}
        event={event}
        breakers={[breakBeforeFirst, breakAfterEach]}
      />,
    );

    expect(
      screen.getAllByRole('link', { name: 'Watch All Videos' }),
    ).toHaveLength(1);
  });

  test('links the playlist to every match video with the event name as its title', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(2)}
        event={event}
        breakers={[breakBeforeFirst]}
      />,
    );

    expect(
      screen
        .getByRole('link', { name: 'Watch All Videos' })
        .getAttribute('href'),
    ).toBe(
      'https://www.youtube.com/watch_videos?video_ids=vid1,vid2&title=Test%20Event',
    );
  });

  test('strips start-time parameters from video ids in the playlist', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={[
          makeMatch({ videos: [{ type: 'youtube', key: 'abc123?t=45' }] }),
        ]}
        event={event}
        breakers={[breakBeforeFirst]}
      />,
    );

    expect(
      screen
        .getByRole('link', { name: 'Watch All Videos' })
        .getAttribute('href'),
    ).toBe(
      'https://www.youtube.com/watch_videos?video_ids=abc123&title=Test%20Event',
    );
  });

  test('offers no playlist when the matches have no YouTube videos', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={[makeMatch({ videos: [{ type: 'tba', key: 'internal' }] })]}
        event={event}
        breakers={[breakBeforeFirst]}
      />,
    );

    expect(screen.queryByRole('link', { name: 'Watch All Videos' })).toBeNull();
  });

  test('splits more than fifty videos into a playlist menu', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={makeMatches(51)}
        event={event}
        breakers={[breakBeforeFirst]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Watch Videos' }));

    expect(
      [
        screen.getByRole('menuitem', { name: 'Videos 1–50' }),
        screen.getByRole('menuitem', { name: 'Videos 51–51' }),
      ].map((item) => item.getAttribute('href')),
    ).toEqual([
      `https://www.youtube.com/watch_videos?video_ids=${Array.from({ length: 50 }, (_, i) => `vid${i + 1}`).join(',')}&title=Test%20Event`,
      'https://www.youtube.com/watch_videos?video_ids=vid51&title=Test%20Event',
    ]);
  });

  test('shows the Nexus status for the matching match key', () => {
    render(
      <SimpleMatchRowsWithBreaks
        matches={[
          makeUnplayedMatch({ key: '2026test_qm1' }),
          makeUnplayedMatch({ key: '2026test_qm2', match_number: 2 }),
        ]}
        event={event}
        breakers={[neverBreak]}
        nexusStatusByKey={{ '2026test_qm2': 'On deck' }}
      />,
    );

    expect(screen.getAllByLabelText(/Nexus status/)).toHaveLength(1);
  });
});

describe('MatchRow', () => {
  test('links the play button to the first video on YouTube with its start time', () => {
    render(
      <MatchRow
        match={makeMatch({
          videos: [
            { type: 'youtube', key: 'abc123?t=45' },
            { type: 'youtube', key: 'second' },
          ],
        })}
        event={event}
        year={2026}
      />,
    );

    expect(linkHrefs()).toContain(
      'https://www.youtube.com/watch?v=abc123&t=45',
    );
  });

  test('shows the Nexus status in place of the play button when there is no video', () => {
    render(
      <MatchRow
        match={makeUnplayedMatch()}
        event={event}
        year={2026}
        nexusStatus="Now queuing"
      />,
    );

    expect(screen.getByLabelText('Nexus status: Now queuing')).toBeTruthy();
  });

  test('reveals the Nexus status text on hover', async () => {
    render(
      <TooltipProvider delay={0}>
        <MatchRow
          match={makeUnplayedMatch()}
          event={event}
          year={2026}
          nexusStatus="On field"
        />
      </TooltipProvider>,
    );

    const trigger = screen.getByLabelText('Nexus status: On field');
    fireEvent.pointerEnter(trigger);
    fireEvent.mouseEnter(trigger);

    expect(await screen.findByText('On field')).toBeTruthy();
  });

  test('prefers the video link over the Nexus status', () => {
    render(
      <MatchRow
        match={makeMatch({ videos: [{ type: 'youtube', key: 'abc123' }] })}
        event={event}
        year={2026}
        nexusStatus="On field"
      />,
    );

    expect(screen.queryByLabelText(/Nexus status/)).toBeNull();
  });

  test('leaves the play column empty without a video or Nexus status', () => {
    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect(linkHrefs()).toEqual([
      '/match/2026test_qm1',
      '/team/254/2026',
      '/team/1114/2026',
      '/team/2056/2026',
      '/team/148/2026',
      '/team/217/2026',
      '/team/33/2026',
    ]);
  });

  test('titles the match for the event playoff format', () => {
    render(
      <MatchRow
        match={makeMatch({
          key: '2026test_sf3m1',
          comp_level: CompLevel.SF,
          set_number: 3,
        })}
        event={event}
        year={2026}
      />,
    );

    expect(screen.getByRole('link', { name: 'Match 3' })).toBeTruthy();
  });

  test('falls back to a custom bracket title when the event has no playoff type', () => {
    render(
      <MatchRow
        match={makeMatch({
          key: '2026test_qf2m1',
          comp_level: CompLevel.QF,
          set_number: 2,
        })}
        event={{ ...event, playoff_type: null }}
        year={2026}
      />,
    );

    expect(
      screen.getByRole('link', { name: 'Quarters 2 Match 1' }),
    ).toBeTruthy();
  });

  test('shows both scores for a played match', () => {
    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect([
      screen.getByText('94').textContent,
      screen.getByText('43').textContent,
    ]).toEqual(['94', '43']);
  });

  test('shows the predicted start time instead of scores for an unplayed match', () => {
    render(
      <MatchRow
        match={makeUnplayedMatch({ predicted_time: 1772893800 })}
        event={event}
        year={2026}
      />,
    );

    expect(screen.getByText(/^\w{3} \d{1,2}:\d{2} [AP]M$/)).toBeTruthy();
  });

  test('shows no scores for an unplayed match', () => {
    render(
      <MatchRow
        match={makeUnplayedMatch({ predicted_time: 1772893800 })}
        event={event}
        year={2026}
      />,
    );

    expect(screen.queryByText('-1')).toBeNull();
  });

  test('shows no time for an unplayed match without a prediction', () => {
    render(<MatchRow match={makeUnplayedMatch()} event={event} year={2026} />);

    expect(screen.queryByText(/[AP]M$/)).toBeNull();
  });

  test('shows the scheduled time for an unplayed match without a prediction', () => {
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('America/New_York');
    render(
      <MatchRow
        match={makeUnplayedMatch({ time: 1772893800 })}
        event={event}
        year={2026}
      />,
    );

    expect(screen.getByText('Sat 9:30 AM')).toBeTruthy();
  });

  test.each([
    { alliance: 'red', focusTeamKey: 'frc254' },
    { alliance: 'blue', focusTeamKey: 'frc217' },
    { alliance: 'neither', focusTeamKey: 'frc9999' },
  ])(
    'still shows both scores when the focus team is on the $alliance alliance',
    ({ focusTeamKey }) => {
      render(
        <MatchRow
          match={makeMatch()}
          event={event}
          year={2026}
          focusTeamKey={focusTeamKey}
        />,
      );

      expect([
        screen.getByText('94').textContent,
        screen.getByText('43').textContent,
      ]).toEqual(['94', '43']);
    },
  );

  test('shows ranking point dots for a qualification match with a breakdown', () => {
    render(
      <MatchRow
        match={makeMatch({
          score_breakdown: {
            red: {
              energizedAchieved: true,
              superchargedAchieved: false,
              traversalAchieved: true,
            },
            blue: {
              energizedAchieved: false,
              superchargedAchieved: false,
              traversalAchieved: false,
            },
          } as unknown as Match['score_breakdown'],
        })}
        event={event}
        year={2026}
      />,
    );

    expect(
      screen.getByLabelText(
        'Energized Bonus (Achieved), Supercharged Bonus (Not Achieved), Traversal Bonus (Achieved)',
      ),
    ).toBeTruthy();
  });

  test('marks the match with a star when a favorite team plays in it', () => {
    mocks.useFavoriteTeamKeys.mockReturnValue({
      teamKeys: ['frc217'],
      isLoading: false,
    });

    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect(screen.getByText('Includes a favorite team')).toBeTruthy();
  });

  test('shows no star when no favorite team plays in the match', () => {
    mocks.useFavoriteTeamKeys.mockReturnValue({
      teamKeys: ['frc604'],
      isLoading: false,
    });

    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect(screen.queryByText('Includes a favorite team')).toBeNull();
  });

  test("marks only the favorite team's number with a dot", () => {
    mocks.useFavoriteTeamKeys.mockReturnValue({
      teamKeys: ['frc217'],
      isLoading: false,
    });

    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect(screen.getByText('Favorite team').closest('div')?.textContent).toBe(
      '217Favorite team',
    );
  });

  test("marks each favorite team's number when several play in the match", () => {
    mocks.useFavoriteTeamKeys.mockReturnValue({
      teamKeys: ['frc254', 'frc33'],
      isLoading: false,
    });

    render(<MatchRow match={makeMatch()} event={event} year={2026} />);

    expect(
      screen
        .getAllByText('Favorite team')
        .map((dot) => dot.closest('div')?.textContent),
    ).toEqual(['254Favorite team', '33Favorite team']);
  });
});

describe('SimpleMatchRow', () => {
  test('shows the team and score headers', () => {
    render(<SimpleMatchRow match={makeMatch()} year={2026} />);

    expect([
      screen.getByText('Teams').textContent,
      screen.getByText('Score').textContent,
    ]).toEqual(['Teams', 'Score']);
  });

  test('links every team on both alliances', () => {
    render(<SimpleMatchRow match={makeMatch()} year={2026} />);

    expect(linkHrefs()).toEqual([
      '/team/254/2026',
      '/team/1114/2026',
      '/team/2056/2026',
      '/team/148/2026',
      '/team/217/2026',
      '/team/33/2026',
    ]);
  });

  test('shows both scores for a played match', () => {
    render(<SimpleMatchRow match={makeMatch()} year={2026} />);

    expect([
      screen.getByText('94').textContent,
      screen.getByText('43').textContent,
    ]).toEqual(['94', '43']);
  });

  test('shows the predicted start time for an unplayed match', () => {
    render(
      <SimpleMatchRow
        match={makeUnplayedMatch({ predicted_time: 1772893800 })}
        year={2026}
      />,
    );

    expect(screen.getByText(/^\w{3} \d{1,2}:\d{2} [AP]M$/)).toBeTruthy();
  });

  test('formats the predicted time with formatMatchTime', () => {
    const predictedTime = new Date(2026, 2, 7, 9, 30).getTime() / 1000;
    render(
      <SimpleMatchRow
        match={makeUnplayedMatch({ predicted_time: predictedTime })}
        year={2026}
      />,
    );

    expect(screen.getByText(formatMatchTime(predictedTime))).toBeTruthy();
  });

  test('shows no time for an unplayed match without a prediction', () => {
    render(<SimpleMatchRow match={makeUnplayedMatch()} year={2026} />);

    expect(screen.queryByText(/[AP]M$/)).toBeNull();
  });

  test('shows the scheduled time for an unplayed match without a prediction', () => {
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('America/New_York');
    render(
      <SimpleMatchRow
        match={makeUnplayedMatch({ time: 1772893800 })}
        year={2026}
      />,
    );

    expect(screen.getByText('Sat 9:30 AM')).toBeTruthy();
  });
});

describe('BreakRow', () => {
  test('shows the break text', () => {
    render(<BreakRow text="Lunch" />);

    expect(screen.getByText('Lunch')).toBeTruthy();
  });

  test('shows the break text at the small size', () => {
    render(<BreakRow text="End of Day" size="small" />);

    expect(screen.getByText('End of Day')).toBeTruthy();
  });

  test('shows no playlist controls when the playlist is empty', () => {
    render(<BreakRow text="Lunch" playlists={[]} />);

    expect(screen.queryByRole('link')).toBeNull();
  });

  test('links directly to a single playlist', () => {
    render(
      <BreakRow
        text="Lunch"
        playlists={[
          {
            url: 'https://www.youtube.com/watch_videos?video_ids=a',
            label: 'Watch All Videos',
          },
        ]}
      />,
    );

    expect(
      screen
        .getByRole('link', { name: 'Watch All Videos' })
        .getAttribute('href'),
    ).toBe('https://www.youtube.com/watch_videos?video_ids=a');
  });

  test('lists multiple playlists in a menu', () => {
    render(
      <BreakRow
        text="Lunch"
        playlists={[
          { url: 'https://example.com/1', label: 'Videos 1–50' },
          { url: 'https://example.com/2', label: 'Videos 51–75' },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Watch Videos' }));

    const menu = screen.getByRole('menu');
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((item) => item.textContent),
    ).toEqual(['Videos 1–50', 'Videos 51–75']);
  });
});
