import { render, screen, within } from '@testing-library/react';
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
});
