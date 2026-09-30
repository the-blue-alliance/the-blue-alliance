import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Event,
  EventType,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import MatchDetails from '~/components/tba/match/matchDetails';
import { formatMatchTime } from '~/lib/matchUtils';

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

vi.mock('~/components/tba/videoEmbeds', () => ({
  YoutubeEmbed: ({ videoId, title }: { videoId: string; title: string }) => (
    <iframe title={title} src={`https://www.youtube.com/embed/${videoId}`} />
  ),
}));

// Each year's breakdown is lazy-loaded; stub them so this file tests only
// which one MatchDetails picks. The breakdowns have their own tests.
vi.mock('~/components/tba/match/scoreBreakdown2015', () => ({
  default: () => <div>ScoreBreakdown2015</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2016', () => ({
  default: () => <div>ScoreBreakdown2016</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2017', () => ({
  default: () => <div>ScoreBreakdown2017</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2018', () => ({
  default: () => <div>ScoreBreakdown2018</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2019', () => ({
  default: () => <div>ScoreBreakdown2019</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2020', () => ({
  default: () => <div>ScoreBreakdown2020</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2022', () => ({
  default: () => <div>ScoreBreakdown2022</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2023', () => ({
  default: () => <div>ScoreBreakdown2023</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2024', () => ({
  default: () => <div>ScoreBreakdown2024</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2025', () => ({
  default: () => <div>ScoreBreakdown2025</div>,
}));
vi.mock('~/components/tba/match/scoreBreakdown2026', () => ({
  default: () => <div>ScoreBreakdown2026</div>,
}));
vi.mock('~/components/tba/match/scoreByShift2026', () => ({
  default: () => <div>ScoreByShift2026</div>,
}));

// A fixed-offset zone (UTC-12) that no viewer's browser will report, so the
// "Show in my timezone" toggle is always offered and the event-local times
// are deterministic.
const EVENT_TIMEZONE = 'Etc/GMT+12';
// 2026-03-07T14:30:00Z, which is 2:30 AM on Sat, Mar 7 in Etc/GMT+12.
const SCHEDULED = 1772893800;

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
  timezone: EVENT_TIMEZONE,
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

function breakdownWith(
  fields: Record<string, unknown>,
): Match['score_breakdown'] {
  return { red: fields, blue: fields } as unknown as Match['score_breakdown'];
}

function renderDetails(match: Match, eventOverrides: Partial<Event> = {}) {
  return render(
    <MatchDetails match={match} event={{ ...event, ...eventOverrides }} />,
  );
}

describe('MatchDetails', () => {
  test('renders the match row with every team linked', () => {
    renderDetails(makeMatch());

    expect(
      screen.getAllByRole('link').map((link) => link.getAttribute('href')),
    ).toEqual([
      '/team/254/2026',
      '/team/1114/2026',
      '/team/2056/2026',
      '/team/148/2026',
      '/team/217/2026',
      '/team/33/2026',
    ]);
  });

  test.each([
    { year: 2015, fields: { container_count_level1: 0 } },
    { year: 2016, fields: { teleopDefensesBreached: false } },
    { year: 2017, fields: { kPaRankingPointAchieved: false } },
    { year: 2018, fields: { autoQuestRankingPoint: false } },
    { year: 2019, fields: { completeRocketRankingPoint: false } },
    { year: 2020, fields: { shieldEnergizedRankingPoint: false } },
    { year: 2022, fields: { cargoBonusRankingPoint: false } },
    { year: 2023, fields: { sustainabilityBonusAchieved: false } },
    { year: 2024, fields: { melodyBonusAchieved: false } },
    { year: 2025, fields: { coralBonusAchieved: false } },
    { year: 2026, fields: { energizedAchieved: false } },
  ])('shows the $year score breakdown', async ({ year, fields }) => {
    renderDetails(makeMatch({ score_breakdown: breakdownWith(fields) }));

    expect(await screen.findByText(`ScoreBreakdown${year}`)).toBeTruthy();
  });

  test('shows the score-by-shift chart alongside the 2026 breakdown', async () => {
    renderDetails(
      makeMatch({
        score_breakdown: breakdownWith({ energizedAchieved: true }),
      }),
    );

    expect(await screen.findByText('ScoreByShift2026')).toBeTruthy();
  });

  test('shows no breakdown when the match has none', () => {
    renderDetails(makeMatch({ score_breakdown: null }));

    expect(screen.queryByText(/^ScoreBreakdown/)).toBeNull();
  });

  test('shows no breakdown when the breakdown shape is unrecognised', () => {
    renderDetails(
      makeMatch({ score_breakdown: breakdownWith({ mysteryPoints: 1 }) }),
    );

    expect(screen.queryByText(/^ScoreBreakdown/)).toBeNull();
  });

  test('embeds each YouTube video titled with the event and match', () => {
    renderDetails(
      makeMatch({
        videos: [
          { type: 'youtube', key: 'abc123' },
          { type: 'tba', key: 'internal' },
          { type: 'youtube', key: 'def456' },
        ],
      }),
    );

    expect(
      [
        screen.getByTitle('Test Event 1 abc123'),
        screen.getByTitle('Test Event 1 def456'),
      ].map((frame) => frame.getAttribute('src')),
    ).toEqual([
      'https://www.youtube.com/embed/abc123',
      'https://www.youtube.com/embed/def456',
    ]);
  });

  test('does not embed non-YouTube videos', () => {
    renderDetails(makeMatch({ videos: [{ type: 'tba', key: 'internal' }] }));

    expect(screen.queryByTitle(/Test Event/)).toBeNull();
  });

  test('shows the match date in the event timezone', () => {
    renderDetails(makeMatch({ time: SCHEDULED }));

    expect(screen.getByText('Date:').parentElement?.textContent).toBe(
      'Date:Sat, Mar 7',
    );
  });

  test('dates the match from the actual start when there is one', () => {
    renderDetails(
      makeMatch({ actual_time: SCHEDULED + 86400, time: SCHEDULED }),
    );

    expect(screen.getByText('Date:').parentElement?.textContent).toBe(
      'Date:Sun, Mar 8',
    );
  });

  test('dates the match from the prediction when there is no schedule', () => {
    renderDetails(makeMatch({ predicted_time: SCHEDULED + 2 * 86400 }));

    expect(screen.getByText('Date:').parentElement?.textContent).toBe(
      'Date:Mon, Mar 9',
    );
  });

  test('shows no date when the match has no times at all', () => {
    renderDetails(makeMatch());

    expect(screen.queryByText('Date:')).toBeNull();
  });

  test('shows the scheduled time in the event timezone', () => {
    renderDetails(makeMatch({ time: SCHEDULED }));

    expect(screen.getByText('Scheduled:').parentElement?.textContent).toMatch(
      /^Scheduled:2:30 AM$/,
    );
  });

  test('shows the predicted time in the event timezone', () => {
    renderDetails(makeMatch({ predicted_time: SCHEDULED + 600 }));

    expect(screen.getByText('Predicted:').parentElement?.textContent).toMatch(
      /^Predicted:2:40 AM$/,
    );
  });

  test('shows the actual time without a comparison when there is no schedule', () => {
    renderDetails(makeMatch({ actual_time: SCHEDULED + 300 }));

    expect(screen.getByText('Actual:').parentElement?.textContent).toMatch(
      /^Actual:2:35 AM$/,
    );
  });

  test.each([
    { offset: 20, difference: 'on time' },
    { offset: -20, difference: 'on time' },
    { offset: 5 * 60, difference: '5m late' },
    { offset: 60 * 60, difference: '1h late' },
    { offset: 65 * 60, difference: '1h 5m late' },
    { offset: -5 * 60, difference: '5m early' },
    { offset: -60 * 60, difference: '1h early' },
    { offset: -65 * 60, difference: '1h 5m early' },
  ])(
    'describes an actual start $offset seconds from schedule as "$difference"',
    ({ offset, difference }) => {
      renderDetails(
        makeMatch({ time: SCHEDULED, actual_time: SCHEDULED + offset }),
      );

      expect(screen.getByText(`(${difference})`)).toBeTruthy();
    },
  );

  test('offers a timezone toggle when the viewer is not in the event timezone', () => {
    renderDetails(makeMatch({ time: SCHEDULED }));

    expect(
      screen.getByRole('checkbox', { name: 'Show in my timezone' }),
    ).toBeTruthy();
  });

  test('hides the timezone toggle when the viewer is in the event timezone', () => {
    renderDetails(makeMatch({ time: SCHEDULED }), {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });

    expect(screen.queryByRole('checkbox')).toBeNull();
  });

  test('falls back to UTC when the event has no timezone', () => {
    renderDetails(makeMatch({ time: SCHEDULED }), { timezone: null });

    expect(screen.getByText('Scheduled:').parentElement?.textContent).toMatch(
      /^Scheduled:2:30 PM$/,
    );
  });

  test('shows times in the viewer timezone once the toggle is checked', () => {
    const viewerTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const expected = formatMatchTime(SCHEDULED, {
      timeZone: viewerTimezone,
      weekday: false,
    });
    renderDetails(makeMatch({ time: SCHEDULED }));

    fireEvent.click(
      screen.getByRole('checkbox', { name: 'Show in my timezone' }),
    );

    expect(screen.getByText('Scheduled:').parentElement?.textContent).toBe(
      `Scheduled:${expected}`,
    );
  });

  test('returns to the event timezone when the toggle is unchecked', () => {
    renderDetails(makeMatch({ time: SCHEDULED }));
    const toggle = screen.getByRole('checkbox', {
      name: 'Show in my timezone',
    });

    fireEvent.click(toggle);
    fireEvent.click(toggle);

    expect(screen.getByText('Scheduled:').parentElement?.textContent).toMatch(
      /^Scheduled:2:30 AM$/,
    );
  });
});
