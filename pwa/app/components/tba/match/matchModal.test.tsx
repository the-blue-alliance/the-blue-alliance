import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Event,
  EventType,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import { MatchModal } from '~/components/tba/match/matchModal';

interface NavigateOptions {
  to: string;
  search: (prev: Record<string, unknown>) => Record<string, unknown>;
  replace: boolean;
  resetScroll: boolean;
}

const { useSearchMock, navigateMock, matchQueryFn, eventQueryFn } = vi.hoisted(
  () => ({
    useSearchMock: vi.fn<() => { matchKey?: string }>(),
    navigateMock: vi.fn<(options: NavigateOptions) => Promise<void>>(),
    matchQueryFn: vi.fn<() => Promise<Match | null>>(),
    eventQueryFn: vi.fn<() => Promise<Event | null>>(),
  }),
);

vi.mock('@tanstack/react-router', () => ({
  useSearch: useSearchMock,
  useRouter: () => ({ navigate: navigateMock }),
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getMatchOptions: ({ path }: { path: { match_key: string } }) => ({
    queryKey: ['match', path.match_key],
    queryFn: matchQueryFn,
  }),
  getEventOptions: ({ path }: { path: { event_key: string } }) => ({
    queryKey: ['event', path.event_key],
    queryFn: eventQueryFn,
  }),
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

vi.mock('~/components/tba/match/matchDetails', () => ({
  default: ({ match, event }: { match: Match; event: Event }) => (
    <div>
      Details for {match.key} at {event.key}
    </div>
  ),
}));

vi.mock('~/components/ui/credenza', () => ({
  Credenza: ({
    children,
    open,
    onOpenChange,
  }: {
    children: ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => (
    <div>
      <dialog open={open}>{children}</dialog>
      <button onClick={() => onOpenChange?.(false)}>Dismiss</button>
      <button onClick={() => onOpenChange?.(true)}>Reopen</button>
    </div>
  ),
  CredenzaBody: ({ children }: { children: ReactNode }) => children,
  CredenzaContent: ({ children }: { children: ReactNode }) => children,
  CredenzaHeader: ({ children }: { children: ReactNode }) => children,
  CredenzaTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
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

const match: Match = {
  key: '2026test_sf2m1',
  comp_level: CompLevel.SF,
  set_number: 2,
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
};

function renderModal() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const ui = (
    <QueryClientProvider client={queryClient}>
      <MatchModal />
    </QueryClientProvider>
  );

  return { ...render(ui), ui };
}

describe('MatchModal', () => {
  beforeEach(() => {
    useSearchMock.mockReturnValue({ matchKey: '2026test_sf2m1' });
    matchQueryFn.mockResolvedValue(match);
    eventQueryFn.mockResolvedValue(event);
  });

  test('stays closed when the URL has no match key', () => {
    useSearchMock.mockReturnValue({});

    renderModal();

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  test('stays closed when the URL match key is malformed', () => {
    useSearchMock.mockReturnValue({ matchKey: 'not-a-match' });

    renderModal();

    expect(screen.queryByRole('dialog')).toBeNull();
  });

  test('opens for a valid match key in the URL', () => {
    renderModal();

    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  test('titles the dialog with the match and event, linked to the match page', async () => {
    renderModal();

    const link = await screen.findByRole('link', {
      name: 'Match 2 - Test Event 2026',
    });
    expect(link.getAttribute('href')).toBe('/match/2026test_sf2m1');
  });

  test('falls back to a custom bracket title when the event has no playoff type', async () => {
    eventQueryFn.mockResolvedValue({ ...event, playoff_type: null });

    renderModal();

    expect(
      await screen.findByRole('link', {
        name: 'Semis 2 Match 1 - Test Event 2026',
      }),
    ).toBeTruthy();
  });

  test('shows the match details for the event derived from the match key', async () => {
    renderModal();

    expect(
      await screen.findByText('Details for 2026test_sf2m1 at 2026test'),
    ).toBeTruthy();
  });

  test('shows a placeholder while the match is loading', () => {
    matchQueryFn.mockReturnValue(new Promise(() => {}));

    renderModal();

    expect(screen.getByRole('heading').textContent).toBe('');
  });

  test('reports a missing match when the match lookup returns nothing', async () => {
    matchQueryFn.mockResolvedValue(null);

    renderModal();

    expect(
      await screen.findByText('The requested match could not be found.'),
    ).toBeTruthy();
  });

  test('reports a missing match when the event lookup returns nothing', async () => {
    eventQueryFn.mockResolvedValue(null);

    renderModal();

    expect(
      await screen.findByRole('heading', { name: 'Match not found' }),
    ).toBeTruthy();
  });

  test('removes the match key from the URL when dismissed', () => {
    renderModal();

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    expect(navigateMock).toHaveBeenCalledWith({
      to: '.',
      search: expect.any(Function),
      replace: true,
      resetScroll: false,
    });
  });

  test('keeps the other search params when dismissed', () => {
    renderModal();

    fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }));

    const { search } = navigateMock.mock.calls[0][0];
    expect(search({ matchKey: '2026test_sf2m1', tab: 'results' })).toEqual({
      matchKey: undefined,
      tab: 'results',
    });
  });

  test('does not navigate when asked to open', () => {
    renderModal();

    fireEvent.click(screen.getByRole('button', { name: 'Reopen' }));

    expect(navigateMock).not.toHaveBeenCalled();
  });

  test('keeps showing the last match while the dialog closes', async () => {
    const { rerender, ui } = renderModal();
    await screen.findByText('Details for 2026test_sf2m1 at 2026test');
    useSearchMock.mockReturnValue({});

    rerender(ui);

    expect(
      screen.getByText('Details for 2026test_sf2m1 at 2026test'),
    ).toBeTruthy();
  });
});
