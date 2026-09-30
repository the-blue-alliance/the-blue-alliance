import { fireEvent, render, screen, within } from '@testing-library/react';
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
import EliminationBracket from '~/components/tba/eliminationBracket';

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
  MatchLink: ({ children }: { children: ReactNode }) => (
    <a href="/match">{children}</a>
  ),
}));

const alliances: EliminationAlliance[] = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ({
  declines: [],
  picks: [`frc${n}01`, `frc${n}02`, `frc${n}03`],
}));

const event: Event = {
  key: '2026test',
  name: 'Test Event',
  event_code: 'test',
  event_type: EventType.REGIONAL,
  district: null,
  city: null,
  state_prov: null,
  country: null,
  start_date: '2026-03-01',
  end_date: '2026-03-03',
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

const match1RedWin: Match = {
  key: '2026test_sf1m1',
  comp_level: CompLevel.SF,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 100,
      team_keys: ['frc101', 'frc102', 'frc103'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 50,
      team_keys: ['frc801', 'frc802', 'frc803'],
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
};

describe('EliminationBracket', () => {
  test('shows a winner placeholder when only alliances are known', () => {
    render(
      <EliminationBracket alliances={alliances} matches={[]} event={event} />,
    );

    expect(screen.getByText('Winner of Match 1')).toBeTruthy();
  });

  test('shows a loser placeholder for a lower bracket match', () => {
    render(
      <EliminationBracket alliances={alliances} matches={[]} event={event} />,
    );

    expect(screen.getByText('Loser of Match 11')).toBeTruthy();
  });

  test('advances the match 1 winner into the match 7 slot', () => {
    render(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );

    expect(screen.getAllByRole('link', { name: '101' })).toHaveLength(2);
  });

  test('marks match 1 as next before playoffs start', () => {
    render(
      <EliminationBracket alliances={alliances} matches={[]} event={event} />,
    );

    expect(
      within(screen.getByRole('group', { name: 'Match 1' })).queryByText(
        'Next',
      ),
    ).not.toBeNull();
  });

  test('moves next to match 2 after match 1 is decided', () => {
    render(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );

    expect(
      within(screen.getByRole('group', { name: 'Match 2' })).queryByText(
        'Next',
      ),
    ).not.toBeNull();
  });

  test('marks the series winner row as the winner', () => {
    render(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );

    const row = screen
      .getAllByRole('link', { name: '101' })[0]
      .closest('[data-winner]');
    expect(row?.getAttribute('data-winner')).toBe('true');
  });

  test('does not mark the series loser row as the winner', () => {
    render(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );

    const row = screen
      .getAllByRole('link', { name: '801' })[0]
      .closest('[data-winner]');
    expect(row?.getAttribute('data-winner')).toBe('false');
  });

  test('renders nothing without alliances', () => {
    const { container } = render(
      <EliminationBracket alliances={[]} matches={[]} event={event} />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('leaves unknown alliance numbers unnamed', () => {
    render(
      <EliminationBracket
        alliances={alliances.slice(0, 4)}
        matches={[]}
        event={event}
      />,
    );
    // Match 1 is alliance 1 vs 8, and there is no alliance 8.
    const match1 = screen.getByRole('group', { name: 'Match 1' });
    expect(match1.textContent).toContain('(#1 vs )');
  });

  test('names Einstein alliances after their divisions', () => {
    render(
      <EliminationBracket
        alliances={alliances.map((a, i) => ({
          ...a,
          name: i === 0 ? 'Archimedes' : i === 7 ? 'Newton' : undefined,
        }))}
        matches={[match1RedWin]}
        event={{ ...event, event_type: EventType.CMP_FINALS }}
      />,
    );
    const match1 = screen.getByRole('group', { name: 'Match 1' });
    expect(match1.textContent).toContain('(Arc vs New)');
  });

  test('hides alliance members who sat out a later-round series', () => {
    const fourTeamAlliances = alliances.map((a, i) => ({
      ...a,
      picks: [...a.picks, `frc${i + 1}04`],
    }));
    const match7: Match = {
      ...match1RedWin,
      key: '2026test_sf7m1',
      set_number: 7,
      alliances: {
        red: { ...match1RedWin.alliances.red },
        blue: {
          ...match1RedWin.alliances.blue,
          team_keys: ['frc201', 'frc202', 'frc203'],
        },
      },
    };
    render(
      <EliminationBracket
        alliances={fourTeamAlliances}
        matches={[match1RedWin, match7]}
        event={event}
      />,
    );
    const match1 = screen.getByRole('group', { name: 'Match 1' });
    const match7Group = screen.getByRole('group', { name: 'Match 7' });
    // Round 1 shows the full alliance; later rounds only who played.
    expect(within(match1).getByRole('link', { name: '104' })).toBeTruthy();
    expect(within(match7Group).queryByRole('link', { name: '104' })).toBeNull();
    expect(within(match7Group).queryByRole('link', { name: '204' })).toBeNull();
    expect(within(match7Group).getByRole('link', { name: '201' })).toBeTruthy();
  });

  test('highlights an alliance across matches on hover', () => {
    render(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );
    const match1 = screen.getByRole('group', { name: 'Match 1' });
    const redRow = within(match1)
      .getByRole('link', { name: '101' })
      .closest<HTMLElement>('[data-highlight]');
    const blueRow = within(match1)
      .getByRole('link', { name: '801' })
      .closest<HTMLElement>('[data-highlight]');
    if (!redRow || !blueRow) {
      throw new Error('Missing alliance rows');
    }

    fireEvent.mouseEnter(redRow);
    expect(redRow.dataset.highlight).toBe('true');
    expect(within(match1).getByText('#1').className).toContain('bg-red-100');
    fireEvent.mouseLeave(redRow);
    expect(redRow.dataset.highlight).toBe('false');

    fireEvent.mouseEnter(blueRow);
    expect(blueRow.dataset.highlight).toBe('true');
    expect(within(match1).getByText('#8').className).toContain('bg-blue-100');
    fireEvent.mouseLeave(blueRow);
    expect(blueRow.dataset.highlight).toBe('false');
  });

  test('re-renders matches when the results change', () => {
    const { rerender } = render(
      <EliminationBracket alliances={alliances} matches={[]} event={event} />,
    );
    expect(screen.getByText('Winner of Match 1')).toBeTruthy();

    rerender(
      <EliminationBracket
        alliances={alliances}
        matches={[match1RedWin]}
        event={event}
      />,
    );
    expect(screen.getAllByRole('link', { name: '101' })).toHaveLength(2);
  });
});
