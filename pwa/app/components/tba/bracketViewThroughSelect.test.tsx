import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Event,
  EventType,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import BracketViewThroughSelect, {
  matchesViewedThrough,
} from '~/components/tba/bracketViewThroughSelect';

function makeMatch(setNumber: number): Match {
  return {
    key: `2026test_sf${setNumber}m1`,
    comp_level: CompLevel.SF,
    set_number: setNumber,
    match_number: 1,
    alliances: {
      red: {
        score: -1,
        team_keys: [],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: -1,
        team_keys: [],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
    },
    winning_alliance: AllianceColor.NO_ALLIANCE,
    event_key: '2026test',
    time: null,
    actual_time: null,
    predicted_time: null,
    post_result_time: null,
    score_breakdown: null,
    videos: [],
  };
}

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

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('matchesViewedThrough', () => {
  test('keeps matches up to and including the chosen match', () => {
    const matches = [makeMatch(1), makeMatch(2), makeMatch(3)];

    expect(matchesViewedThrough(matches, '2').map((m) => m.set_number)).toEqual(
      [1, 2],
    );
  });

  test('keeps every match when viewing all matches', () => {
    const matches = [makeMatch(1), makeMatch(2)];

    expect(matchesViewedThrough(matches, 'all')).toHaveLength(2);
  });
});

describe('BracketViewThroughSelect', () => {
  test('shows the select outside production', () => {
    render(
      <BracketViewThroughSelect
        matches={[makeMatch(1)]}
        event={event}
        value="all"
        onValueChange={() => {}}
      />,
    );

    expect(screen.getByLabelText('View from Match')).toBeTruthy();
  });

  test('hides the select in production', () => {
    vi.stubEnv('PROD', true);

    render(
      <BracketViewThroughSelect
        matches={[makeMatch(1)]}
        event={event}
        value="all"
        onValueChange={() => {}}
      />,
    );

    expect(screen.queryByLabelText('View from Match')).toBeNull();
  });
});
