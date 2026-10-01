import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { type AnchorHTMLAttributes, type ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type EliminationAlliance,
  type Event,
  EventType,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import DoubleElim4TeamBracket from '~/components/tba/doubleElim4TeamBracket';

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({
    teamKey,
    year,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & {
    teamKey: string;
    year: number;
  }) => (
    <a href={`/team/${teamKey.substring(3)}/${year}`} {...props}>
      {teamKey.substring(3)}
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

/** Alliance n is teams n01, n02, n03 plus backup n04. */
const alliances: EliminationAlliance[] = [1, 2, 3, 4].map((n) => ({
  declines: [],
  picks: [`frc${n}01`, `frc${n}02`, `frc${n}03`, `frc${n}04`],
}));

function allianceTeams(n: number): string[] {
  return [`frc${n}01`, `frc${n}02`, `frc${n}03`];
}

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    key: '2026test',
    name: 'Test Event',
    event_code: 'test',
    event_type: EventType.DISTRICT,
    district: null,
    city: null,
    state_prov: null,
    country: null,
    start_date: '2026-03-01',
    end_date: '2026-03-03',
    year: 2026,
    short_name: null,
    event_type_string: 'District',
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
    playoff_type: PlayoffType.DOUBLE_ELIM_4_TEAM,
    playoff_type_string: null,
    remap_teams: null,
    ...overrides,
  };
}

function makeMatch(
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
  return {
    key: `2026test_${compLevel}${setNumber}m${matchNumber}`,
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
    event_key: '2026test',
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  };
}

// Match 1: 1 v 4 (1 wins). Match 2: 2 v 3 (3 wins).
// Match 3: 1 v 3 (1 wins). Match 4: 4 v 2 (2 wins).
// Match 5: 3 v 2 (3 wins). Finals: 1 v 3, split 1-1 (given out of order).
const fullPlayoffs: Match[] = [
  makeMatch(CompLevel.SF, 1, 1, allianceTeams(1), allianceTeams(4), 50, 20),
  makeMatch(CompLevel.SF, 2, 1, allianceTeams(2), allianceTeams(3), 10, 30),
  makeMatch(CompLevel.SF, 3, 1, allianceTeams(1), allianceTeams(3), 40, 35),
  makeMatch(CompLevel.SF, 4, 1, allianceTeams(4), allianceTeams(2), 15, 25),
  makeMatch(CompLevel.SF, 5, 1, allianceTeams(3), allianceTeams(2), 45, 25),
  makeMatch(CompLevel.F, 1, 2, allianceTeams(1), allianceTeams(3), 30, 60),
  makeMatch(CompLevel.F, 1, 1, allianceTeams(1), allianceTeams(3), 60, 30),
];

function group(label: string): HTMLElement {
  return screen.getByRole('group', { name: label });
}

function rowIn(label: string, teamNumber: string): HTMLElement {
  const row = within(group(label))
    .getByRole('link', { name: teamNumber })
    .closest('[data-winner]');
  if (!(row instanceof HTMLElement)) throw new Error('row not found');
  return row;
}

describe('DoubleElim4TeamBracket', () => {
  test('renders nothing without alliances', () => {
    const { container } = render(
      <DoubleElim4TeamBracket
        alliances={[]}
        matches={fullPlayoffs}
        event={makeEvent()}
      />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('shows seeded placeholders before any match is played', () => {
    render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={[]}
        event={makeEvent()}
      />,
    );

    expect(screen.getByText('Playoff Bracket')).toBeTruthy();
    expect(screen.getByText('Upper Bracket')).toBeTruthy();
    expect(screen.getByText('Lower Bracket')).toBeTruthy();
    expect(group('Match 1').textContent).toContain('#1 vs #4');
    expect(group('Match 2').textContent).toContain('#2 vs #3');
    expect(within(group('Match 1')).getByText('Next')).toBeTruthy();
    expect(
      within(group('Match 3')).getByText('Winner of Match 1'),
    ).toBeTruthy();
    expect(within(group('Match 4')).getByText('Loser of Match 1')).toBeTruthy();
    expect(within(group('Match 5')).getByText('Loser of Match 3')).toBeTruthy();
    expect(within(group('Finals')).getByText('Winner of Match 5')).toBeTruthy();
  });

  test('renders every series with scores, links and the full alliance in round 1', () => {
    render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={fullPlayoffs}
        event={makeEvent()}
      />,
    );

    const match1 = group('Match 1');
    expect(match1.textContent).toContain('#1 vs #4');
    expect(rowIn('Match 1', '101').getAttribute('data-winner')).toBe('true');
    expect(rowIn('Match 1', '401').getAttribute('data-winner')).toBe('false');
    expect(rowIn('Match 1', '101').textContent).toContain('50');
    // Round-1 cards show backups who never played, marked with a dotted line.
    const backup = within(match1).getByRole('link', { name: '104' });
    expect(backup.parentElement?.className).toContain('decoration-dotted');
    expect(
      within(match1).getByRole('link', { name: '101' }).parentElement
        ?.className,
    ).not.toContain('decoration-dotted');
    // Later rounds hide them.
    expect(
      within(group('Match 3')).queryByRole('link', { name: '104' }),
    ).toBeNull();
    expect(
      within(group('Finals')).queryByRole('link', { name: '304' }),
    ).toBeNull();

    // Finals lists both matches, sorted, with the last one deciding the series.
    const finals = group('Finals');
    expect(finals.querySelector('a[href="/match/2026test_f1m1"]')).toBeTruthy();
    expect(finals.querySelector('a[href="/match/2026test_f1m2"]')).toBeTruthy();
    expect(rowIn('Finals', '101').textContent).toContain('6030');
    expect(rowIn('Finals', '301').textContent).toContain('3060');
    expect(rowIn('Finals', '301').getAttribute('data-winner')).toBe('true');
    expect(screen.queryByText('Next')).toBeNull();
  });

  test('marks the next unplayed series and shows dashes for its scores', () => {
    const matches = [
      ...fullPlayoffs.slice(0, 2),
      makeMatch(CompLevel.SF, 3, 1, allianceTeams(1), allianceTeams(3), -1, -1),
    ];

    render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent()}
      />,
    );

    const match3 = group('Match 3');
    expect(within(match3).getByText('Next')).toBeTruthy();
    expect(rowIn('Match 3', '101').textContent).toContain('-');
    expect(rowIn('Match 3', '101').getAttribute('data-winner')).toBe('false');
    expect(group('Match 4').textContent).toContain('#4 vs #2');
  });

  test('highlights an alliance across the bracket while hovering', () => {
    render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={fullPlayoffs}
        event={makeEvent()}
      />,
    );

    fireEvent.mouseEnter(rowIn('Match 1', '101'));
    expect(rowIn('Match 1', '101').getAttribute('data-highlight')).toBe('true');
    expect(rowIn('Match 3', '101').getAttribute('data-highlight')).toBe('true');
    expect(rowIn('Finals', '101').getAttribute('data-highlight')).toBe('true');
    expect(rowIn('Finals', '301').getAttribute('data-highlight')).toBe('false');
    expect(group('Match 1').className).toContain('ring-alliance-red-accent');
    expect(group('Finals').className).toContain('ring-alliance-blue-accent');

    fireEvent.mouseLeave(rowIn('Match 1', '101'));
    expect(rowIn('Match 1', '101').getAttribute('data-highlight')).toBe(
      'false',
    );

    fireEvent.mouseEnter(rowIn('Match 2', '301'));
    expect(rowIn('Match 2', '301').getAttribute('data-highlight')).toBe('true');
    expect(rowIn('Match 5', '301').getAttribute('data-highlight')).toBe('true');
    fireEvent.mouseLeave(rowIn('Match 2', '301'));
    expect(rowIn('Match 2', '301').getAttribute('data-highlight')).toBe(
      'false',
    );
  });

  test('draws advancement paths once the container has a size', async () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      left: 0,
      top: 0,
      right: 100,
      bottom: 100,
      width: 100,
      height: 100,
      toJSON: () => ({}),
    });

    const { container } = render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={fullPlayoffs}
        event={makeEvent()}
      />,
    );

    await waitFor(() =>
      expect(container.querySelectorAll('svg.absolute path')).toHaveLength(5),
    );
  });

  test('re-renders cards when the matches change', () => {
    const { rerender } = render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={fullPlayoffs}
        event={makeEvent()}
      />,
    );
    expect(rowIn('Match 1', '101').textContent).toContain('50');

    rerender(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={[
          makeMatch(
            CompLevel.SF,
            1,
            1,
            allianceTeams(1),
            allianceTeams(4),
            99,
            1,
          ),
        ]}
        event={makeEvent()}
      />,
    );
    expect(rowIn('Match 1', '101').textContent).toContain('99');
    expect(within(group('Match 2')).getByText('Next')).toBeTruthy();
  });

  test('uses division short names at the championship finals', () => {
    const named: EliminationAlliance[] = [
      { name: 'Newton Division', declines: [], picks: allianceTeams(1) },
      { name: 'Archimedes Division', declines: [], picks: allianceTeams(2) },
      { name: 'Curie Division', declines: [], picks: allianceTeams(3) },
      { name: 'Hopper Division', declines: [], picks: allianceTeams(4) },
    ];

    render(
      <DoubleElim4TeamBracket
        alliances={named}
        matches={fullPlayoffs.slice(0, 1)}
        event={makeEvent({ event_type: EventType.CMP_FINALS })}
      />,
    );

    expect(group('Match 1').textContent).toContain('New vs Hop');
    expect(group('Match 2').textContent).toContain('Arc vs Cur');
  });

  test('falls back to match teams when they are in no alliance', () => {
    // This test only checks that rows render and hover safely.
    const matches = [
      makeMatch(
        CompLevel.SF,
        1,
        1,
        ['frc9001', 'frc9002', 'frc9003'],
        ['frc9101', 'frc9102', 'frc9103'],
        10,
        5,
      ),
    ];

    render(
      <DoubleElim4TeamBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent()}
      />,
    );

    const match1 = group('Match 1');
    expect(match1.textContent).not.toContain('vs');
    expect(rowIn('Match 1', '9001')).toBeTruthy();
    expect(rowIn('Match 1', '9101')).toBeTruthy();

    // Hovering either row is inert and doesn't throw.
    fireEvent.mouseEnter(rowIn('Match 1', '9001'));
    fireEvent.mouseLeave(rowIn('Match 1', '9001'));
    fireEvent.mouseEnter(rowIn('Match 1', '9101'));
    fireEvent.mouseLeave(rowIn('Match 1', '9101'));
  });
});
