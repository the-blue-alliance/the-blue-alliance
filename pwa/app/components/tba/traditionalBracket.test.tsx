import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
import TraditionalBracket from '~/components/tba/traditionalBracket';

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

/** Alliance n is teams n01, n02, n03 (alliance 1 also carries backup 104). */
const alliances: EliminationAlliance[] = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ({
  declines: [],
  picks: [
    `frc${n}01`,
    `frc${n}02`,
    `frc${n}03`,
    ...(n === 1 ? ['frc104'] : []),
  ],
}));

function allianceTeams(n: number): string[] {
  return [`frc${n}01`, `frc${n}02`, `frc${n}03`];
}

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    key: '2022test',
    name: 'Test Event',
    event_code: 'test',
    event_type: EventType.REGIONAL,
    district: null,
    city: null,
    state_prov: null,
    country: null,
    start_date: '2022-03-01',
    end_date: '2022-03-03',
    year: 2022,
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
    playoff_type: PlayoffType.BRACKET_8_TEAM,
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
    key: `2022test_${compLevel}${compLevel === CompLevel.QM ? '' : `${setNumber}m`}${matchNumber}`,
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
    event_key: '2022test',
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  };
}

const eightTeamMatches: Match[] = [
  // Quals are ignored by the bracket.
  makeMatch(
    CompLevel.QM,
    1,
    1,
    ['frc9991', 'frc9992', 'frc9993'],
    allianceTeams(2),
    10,
    5,
  ),
  // QF1: alliance 1 sweeps alliance 8 in two matches (given out of order).
  makeMatch(CompLevel.QF, 1, 2, allianceTeams(1), allianceTeams(8), 60, 40),
  makeMatch(CompLevel.QF, 1, 1, allianceTeams(1), allianceTeams(8), 50, 40),
  // QF2: alliance 5 upsets alliance 4 after a tie.
  makeMatch(CompLevel.QF, 2, 1, allianceTeams(4), allianceTeams(5), 30, 30),
  makeMatch(CompLevel.QF, 2, 2, allianceTeams(4), allianceTeams(5), 20, 35),
  // QF3 is scheduled but unplayed.
  makeMatch(CompLevel.QF, 3, 1, allianceTeams(2), allianceTeams(7), -1, -1),
  // SF1: alliance 1 vs alliance 5, blue wins the first match.
  makeMatch(CompLevel.SF, 1, 1, allianceTeams(1), allianceTeams(5), 10, 20),
];

function rowFor(teamNumber: string): HTMLElement {
  const row = screen
    .getAllByRole('link', { name: teamNumber })[0]
    .closest('[data-winner]');
  if (!(row instanceof HTMLElement)) throw new Error('row not found');
  return row;
}

function cardFor(teamNumber: string): HTMLElement {
  const card = rowFor(teamNumber).parentElement;
  if (!card) throw new Error('card not found');
  return card;
}

describe('TraditionalBracket', () => {
  test('renders nothing without alliances or matches', () => {
    const { container, unmount } = render(
      <TraditionalBracket
        alliances={[]}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );
    expect(container.innerHTML).toBe('');
    unmount();

    const { container: noMatches } = render(
      <TraditionalBracket
        alliances={alliances}
        matches={[]}
        event={makeEvent()}
      />,
    );
    expect(noMatches.innerHTML).toBe('');
  });

  test('lays out quarters, semis and finals for an 8-team bracket', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    expect(screen.getByText('Playoff Bracket')).toBeTruthy();
    expect(screen.queryByText('Eighths')).toBeNull();
    expect(screen.getByText('Quarters')).toBeTruthy();
    expect(screen.getByText('Semis')).toBeTruthy();
    expect(screen.getByText('Finals')).toBeTruthy();
    // Qual matches never appear.
    expect(screen.queryByRole('link', { name: '9991' })).toBeNull();
    expect(screen.getByText('QF 1')).toBeTruthy();
    expect(screen.getByText('QF 2')).toBeTruthy();
    expect(screen.getByText('SF 1')).toBeTruthy();
  });

  test('labels each series with alliance numbers and per-match scores in order', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    const qf1 = cardFor('801');
    expect(qf1.textContent).toContain('#1 vs #8');
    const redRow = rowFor('101');
    expect(redRow.getAttribute('data-winner')).toBe('true');
    expect(redRow.textContent).toContain('5060');
    const blueRow = rowFor('801');
    expect(blueRow.getAttribute('data-winner')).toBe('false');
    expect(blueRow.textContent).toContain('4040');
    // Both matches link out.
    expect(qf1.querySelector('a[href="/match/2022test_qf1m1"]')).toBeTruthy();
    expect(qf1.querySelector('a[href="/match/2022test_qf1m2"]')).toBeTruthy();
  });

  test('decides the series by the last match', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    expect(rowFor('501').getAttribute('data-winner')).toBe('true');
    expect(rowFor('401').getAttribute('data-winner')).toBe('false');
  });

  test('shows dashes for unplayed matches', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    const row = rowFor('701');
    expect(row.textContent).toContain('-');
    expect(row.getAttribute('data-winner')).toBe('false');
  });

  test('hides alliance members who did not play in the series', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    expect(screen.queryByRole('link', { name: '104' })).toBeNull();
  });

  test('highlights every card an alliance played in while hovering its row', () => {
    render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    const qf1Red = rowFor('101');
    fireEvent.mouseEnter(qf1Red);

    // Alliance 1 appears in QF1 (won) and SF1 (lost).
    const [qf1Link, sf1Link] = screen.getAllByRole('link', { name: '101' });
    const qf1Row = qf1Link.closest('[data-winner]');
    const sf1Row = sf1Link.closest('[data-winner]');
    expect(qf1Row?.getAttribute('data-highlight')).toBe('true');
    expect(sf1Row?.getAttribute('data-highlight')).toBe('true');
    expect(qf1Row?.parentElement?.className).toContain(
      'ring-alliance-red-accent',
    );
    expect(sf1Row?.parentElement?.className).toContain(
      'ring-alliance-blue-accent',
    );
    expect(rowFor('801').getAttribute('data-highlight')).toBe('false');

    fireEvent.mouseLeave(qf1Red);
    expect(qf1Row?.getAttribute('data-highlight')).toBe('false');

    // Hovering the blue side highlights the blue alliance instead.
    fireEvent.mouseEnter(rowFor('501'));
    expect(rowFor('501').getAttribute('data-highlight')).toBe('true');
    expect(qf1Row?.getAttribute('data-highlight')).toBe('false');
    fireEvent.mouseLeave(rowFor('501'));
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
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );

    // QF1 -> SF1 and QF2 -> SF1 are decided. SF1 -> Finals is too, but the
    // finals card has no matches and so no element to draw to.
    await waitFor(() =>
      expect(container.querySelectorAll('svg.absolute path')).toHaveLength(2),
    );
  });

  test('re-renders cards when the matches change', () => {
    const { rerender } = render(
      <TraditionalBracket
        alliances={alliances}
        matches={eightTeamMatches}
        event={makeEvent()}
      />,
    );
    expect(rowFor('101').textContent).toContain('5060');

    rerender(
      <TraditionalBracket
        alliances={alliances}
        matches={[
          makeMatch(
            CompLevel.QF,
            1,
            1,
            allianceTeams(1),
            allianceTeams(8),
            99,
            1,
          ),
        ]}
        event={makeEvent()}
      />,
    );
    expect(rowFor('101').textContent).toContain('99');
    expect(rowFor('101').textContent).not.toContain('5060');
  });

  test('includes an eighths column when eighth-final matches exist', () => {
    const matches = [
      makeMatch(CompLevel.EF, 1, 1, allianceTeams(1), allianceTeams(8), 10, 5),
      makeMatch(CompLevel.EF, 8, 1, allianceTeams(2), allianceTeams(7), 5, 10),
      ...eightTeamMatches,
    ];

    render(
      <TraditionalBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent({ playoff_type: PlayoffType.BRACKET_16_TEAM })}
      />,
    );

    expect(screen.getByText('Eighths')).toBeTruthy();
    expect(screen.getByText('EF 1')).toBeTruthy();
    expect(screen.getByText('EF 8')).toBeTruthy();
    expect(screen.getByText('Quarters')).toBeTruthy();
  });

  test('skips the quarters column for 4- and 2-team brackets', () => {
    const matches = [
      makeMatch(CompLevel.SF, 1, 1, allianceTeams(1), allianceTeams(4), 10, 5),
      makeMatch(CompLevel.SF, 2, 1, allianceTeams(2), allianceTeams(3), 5, 10),
      makeMatch(CompLevel.F, 1, 1, allianceTeams(1), allianceTeams(3), 10, 5),
    ];

    const { unmount } = render(
      <TraditionalBracket
        alliances={alliances.slice(0, 4)}
        matches={matches}
        event={makeEvent({ playoff_type: PlayoffType.BRACKET_4_TEAM })}
      />,
    );
    expect(screen.queryByText('Quarters')).toBeNull();
    expect(screen.getByText('Semis')).toBeTruthy();
    expect(rowFor('301').getAttribute('data-winner')).toBe('true');
    unmount();

    render(
      <TraditionalBracket
        alliances={alliances.slice(0, 2)}
        matches={[matches[2]]}
        event={makeEvent({ playoff_type: PlayoffType.BRACKET_2_TEAM })}
      />,
    );
    expect(screen.queryByText('Quarters')).toBeNull();
  });

  test('uses division short names at the championship finals', () => {
    const named: EliminationAlliance[] = [
      { name: 'Newton Division', declines: [], picks: allianceTeams(1) },
      { name: 'Archimedes Division', declines: [], picks: allianceTeams(2) },
    ];
    const matches = [
      makeMatch(CompLevel.F, 1, 1, allianceTeams(1), allianceTeams(2), 10, 5),
    ];

    render(
      <TraditionalBracket
        alliances={named}
        matches={matches}
        event={makeEvent({
          event_type: EventType.CMP_FINALS,
          playoff_type: PlayoffType.BRACKET_2_TEAM,
        })}
      />,
    );

    expect(cardFor('101').textContent).toContain('New vs Arc');
  });

  test('falls back to the match teams when they are not in any alliance', () => {
    const matches = [
      makeMatch(
        CompLevel.SF,
        1,
        1,
        ['frc9001', 'frc9002', 'frc9003'],
        allianceTeams(2),
        10,
        5,
      ),
    ];

    render(
      <TraditionalBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent()}
      />,
    );

    const card = cardFor('9001');
    expect(card.textContent).not.toContain('vs');
    expect(screen.getByRole('link', { name: '9001' })).toBeTruthy();
    expect(screen.getByRole('link', { name: '201' })).toBeTruthy();
  });

  // Wrong today: a row whose teams are in no alliance gets alliance number
  // null, which equals the "nothing hovered" null (null === null), so the
  // rows render highlighted, and the winner's card ringed, before any hover.
  // Correct: nothing is highlighted until an alliance is hovered.
  test('Bug #60: does not highlight rows for teams in no alliance before hover', () => {
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
      <TraditionalBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent()}
      />,
    );

    expect(rowFor('9001').getAttribute('data-highlight')).toBe('false');
    expect(rowFor('9101').getAttribute('data-highlight')).toBe('false');
    expect(cardFor('9001').className).not.toContain('ring-alliance-red-accent');
  });

  test('renders an alliance that is missing from the alliance list', () => {
    // Whether these rows start highlighted is Bug #60, covered by its own
    // failing-test PR; this test only checks they render and hover safely.
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
      <TraditionalBracket
        alliances={alliances}
        matches={matches}
        event={makeEvent()}
      />,
    );

    expect(rowFor('9001')).toBeTruthy();
    expect(rowFor('9101')).toBeTruthy();

    // Hovering either row is inert and doesn't throw.
    fireEvent.mouseEnter(rowFor('9001'));
    fireEvent.mouseLeave(rowFor('9001'));
    fireEvent.mouseEnter(rowFor('9101'));
    fireEvent.mouseLeave(rowFor('9101'));
  });
});
