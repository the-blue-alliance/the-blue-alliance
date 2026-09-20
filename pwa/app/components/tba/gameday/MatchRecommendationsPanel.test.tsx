import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, PropsWithChildren } from 'react';
import { Temporal } from 'temporal-polyfill';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { MatchSuggestion } from '~/api/firebase';
import {
  MatchRecommendationsPanel,
  formatMatchTime,
  sortMatchSuggestions,
} from '~/components/tba/gameday/MatchRecommendationsPanel';
import type { UseFirebaseMatchSuggestionsResult } from '~/lib/gameday/useFirebaseMatchSuggestions';

const { useMatchSuggestionsMock } = vi.hoisted(() => ({
  useMatchSuggestionsMock: vi.fn<() => UseFirebaseMatchSuggestionsResult>(),
}));

vi.mock('~/lib/gameday/useFirebaseMatchSuggestions', () => ({
  useFirebaseMatchSuggestions: useMatchSuggestionsMock,
}));

vi.mock('~/components/tba/links', () => ({
  EventLink: ({
    eventOrKey,
    children,
    ...props
  }: PropsWithChildren<
    { eventOrKey: string } & AnchorHTMLAttributes<HTMLAnchorElement>
  >) => (
    <a href={`/event/${eventOrKey}`} {...props}>
      {children}
    </a>
  ),
  MatchLink: ({
    matchOrKey,
    children,
    noModal: _noModal,
    ...props
  }: PropsWithChildren<
    {
      matchOrKey: string;
      noModal?: boolean;
    } & AnchorHTMLAttributes<HTMLAnchorElement>
  >) => (
    <a href={`/match/${matchOrKey}`} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({
    teamKey,
    ...props
  }: { teamKey: string } & AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={`/team/${teamKey.slice(3)}`} {...props}>
      {teamKey.slice(3)}
    </a>
  ),
}));

function makeSuggestion(
  matchKey: string,
  overrides: Partial<MatchSuggestion> = {},
): MatchSuggestion {
  return {
    mk: matchKey,
    ek: '2026miket',
    en: 'Kettering University Event #1',
    esn: 'Kettering #1',
    cl: 'qm',
    sn: 1,
    mn: 12,
    dn: 'Q12',
    rt: [1, 2, 3],
    bt: [4, 5, 6],
    pt: 1_776_960_000,
    st: 1_776_959_700,
    r: 0,
    sc: 0.8,
    c: { f: 0.5, sig: 0.5, td: 0.5, hs: 0.5, cs: 0.5 },
    ...overrides,
  };
}

describe('sortMatchSuggestions', () => {
  test('sorts matches by descending recommendation score', () => {
    const suggestions = [
      makeSuggestion('low', { sc: 0.2 }),
      makeSuggestion('high', { sc: 0.9 }),
    ];

    expect(sortMatchSuggestions(suggestions).map((match) => match.mk)).toEqual([
      'high',
      'low',
    ]);
  });

  test('uses rank to break equal-score ties', () => {
    const suggestions = [
      makeSuggestion('second', { sc: 0.8, r: 2 }),
      makeSuggestion('first', { sc: 0.8, r: 1 }),
    ];

    expect(sortMatchSuggestions(suggestions).map((match) => match.mk)).toEqual([
      'first',
      'second',
    ]);
  });
});

describe('formatMatchTime', () => {
  test('shows relative and viewer-local time', () => {
    const now = Temporal.Instant.from('2026-04-23T15:50:00Z');
    const timestamp = Temporal.Instant.from(
      '2026-04-23T16:00:00Z',
    ).epochMilliseconds;

    expect(formatMatchTime(timestamp / 1000, now, 'America/New_York')).toBe(
      'in 10 min · 12:00 PM',
    );
  });

  test('shows a fallback when time is absent', () => {
    expect(
      formatMatchTime(
        undefined,
        Temporal.Instant.from('2026-04-23T15:50:00Z'),
        'UTC',
      ),
    ).toBe('Time unavailable');
  });
});

describe('MatchRecommendationsPanel', () => {
  beforeEach(() => {
    vi.spyOn(Temporal.Now, 'instant').mockReturnValue(
      Temporal.Instant.fromEpochMilliseconds(1_776_959_400_000),
    );
    vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('UTC');
    useMatchSuggestionsMock.mockReturnValue({
      data: {
        updated_at: 1_776_959_400,
        suggestions: { match: makeSuggestion('2026miket_qm12') },
      },
      error: null,
      isLoading: false,
    });
  });

  test('shows event, match, and team links', () => {
    render(<MatchRecommendationsPanel />);

    expect(
      screen.getAllByRole('link').map((link) => link.getAttribute('href')),
    ).toEqual([
      '/event/2026miket',
      '/match/2026miket_qm12',
      '/team/1',
      '/team/2',
      '/team/3',
      '/team/4',
      '/team/5',
      '/team/6',
    ]);
  });

  test('uses predicted time before scheduled time', () => {
    render(<MatchRecommendationsPanel />);

    expect(screen.getByText('in 10 min · 4:00 PM').textContent).toBe(
      'in 10 min · 4:00 PM',
    );
  });

  test('shows the recommendation score breakdown', () => {
    render(<MatchRecommendationsPanel />);

    expect(
      screen
        .getAllByRole('definition')
        .map((definition) => definition.textContent),
    ).toEqual(['0.80', '0.50', '0.50', '0.50', '0.50', '0.50']);
  });

  test('uses scheduled time when predicted time is absent', () => {
    useMatchSuggestionsMock.mockReturnValue({
      data: {
        updated_at: 1_776_959_400,
        suggestions: {
          match: makeSuggestion('2026miket_qm12', {
            pt: undefined,
            st: 1_776_959_700,
          }),
        },
      },
      error: null,
      isLoading: false,
    });

    render(<MatchRecommendationsPanel />);

    expect(screen.getByText('in 5 min · 3:55 PM').textContent).toBe(
      'in 5 min · 3:55 PM',
    );
  });

  test('shows TBD when Firebase omits empty alliance team lists', () => {
    useMatchSuggestionsMock.mockReturnValue({
      data: {
        updated_at: 1_776_959_400,
        suggestions: {
          match: {
            ...makeSuggestion('2026cc_sf5m1'),
            rt: undefined,
            bt: undefined,
          } as unknown as MatchSuggestion,
        },
      },
      error: null,
      isLoading: false,
    });

    render(<MatchRecommendationsPanel />);

    expect(screen.getAllByText('TBD')).toHaveLength(2);
  });

  test('shows an empty state when there are no recommendations', () => {
    useMatchSuggestionsMock.mockReturnValue({
      data: { updated_at: 1_776_959_400 },
      error: null,
      isLoading: false,
    });

    render(<MatchRecommendationsPanel />);

    expect(
      screen.getByText('No upcoming match recommendations').textContent,
    ).toBe('No upcoming match recommendations');
  });

  test('shows an error when the subscription fails', () => {
    useMatchSuggestionsMock.mockReturnValue({
      data: undefined,
      error: new Error('permission denied'),
      isLoading: false,
    });

    render(<MatchRecommendationsPanel />);

    expect(
      screen.getByText('Unable to load match recommendations').textContent,
    ).toBe('Unable to load match recommendations');
  });
});
