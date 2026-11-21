import {
  AllianceColor,
  CompLevel,
  type Event,
  EventType,
  type Match,
  type MatchAlliance,
} from '~/api/tba/read';

export function makeAlliance(
  score: number,
  teamKeys: string[],
  overrides: Partial<MatchAlliance> = {},
): MatchAlliance {
  return {
    score,
    team_keys: teamKeys,
    surrogate_team_keys: [],
    dq_team_keys: [],
    ...overrides,
  };
}

export function winningAlliance(
  redScore: number,
  blueScore: number,
): AllianceColor {
  if (redScore > blueScore) {
    return AllianceColor.RED;
  }
  if (blueScore > redScore) {
    return AllianceColor.BLUE;
  }
  return AllianceColor.NO_ALLIANCE;
}

export function makeMatch(overrides: Partial<Match> = {}): Match {
  return {
    key: '2026test_qm1',
    comp_level: CompLevel.QM,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: makeAlliance(94, ['frc254', 'frc1114', 'frc2056']),
      blue: makeAlliance(43, ['frc148', 'frc217', 'frc33']),
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

export function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
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
    playoff_type: null,
    playoff_type_string: null,
    remap_teams: null,
    ...overrides,
  };
}
