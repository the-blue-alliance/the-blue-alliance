import { fireEvent, screen } from '@testing-library/react';
import { HttpResponse, delay } from 'msw';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { CompLevel, type Event, type Match, PlayoffType } from '~/api/tba/read';
import { getEvent, getMatch } from '~/api/tba/read/sdk.gen';
import { MatchModal } from '~/components/tba/match/matchModal';
import { makeEvent, makeMatch } from '~/test/factories';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderWithClient } from '~/test/render';

interface NavigateOptions {
  to: string;
  search: (prev: Record<string, unknown>) => Record<string, unknown>;
  replace: boolean;
  resetScroll: boolean;
}

const { useSearchMock, navigateMock } = vi.hoisted(() => ({
  useSearchMock: vi.fn<() => { matchKey?: string }>(),
  navigateMock: vi.fn<(options: NavigateOptions) => Promise<void>>(),
}));

vi.mock('@tanstack/react-router', () => ({
  useSearch: useSearchMock,
  useRouter: () => ({ navigate: navigateMock }),
}));

vi.mock('~/components/tba/links', () => import('~/test/linkMocks'));

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

const event = makeEvent({
  start_date: '2026-03-06',
  end_date: '2026-03-08',
  playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
});

const match = makeMatch({
  key: '2026test_sf2m1',
  comp_level: CompLevel.SF,
  set_number: 2,
});

const MATCH_PATH = { path: { match_key: '2026test_sf2m1' } };
const EVENT_PATH = { path: { event_key: '2026test' } };

function renderModal() {
  return renderWithClient(<MatchModal />);
}

describe('MatchModal', () => {
  beforeEach(() => {
    useSearchMock.mockReturnValue({ matchKey: '2026test_sf2m1' });
    mockTbaApi(getMatch, MATCH_PATH, match);
    mockTbaApi(getEvent, EVENT_PATH, event);
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
    mockTbaApi(getEvent, EVENT_PATH, { ...event, playoff_type: null });

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
    mockTbaApiWith(getMatch, MATCH_PATH, () => delay('infinite'));

    renderModal();

    expect(screen.getByRole('heading').textContent).toBe('');
  });

  test('reports a missing match when the match lookup returns nothing', async () => {
    mockTbaApiWith(
      getMatch,
      MATCH_PATH,
      () => new HttpResponse(null, { status: 404 }),
    );

    renderModal();

    expect(
      await screen.findByText('The requested match could not be found.'),
    ).toBeTruthy();
  });

  test('reports a missing match when the event lookup returns nothing', async () => {
    mockTbaApiWith(
      getEvent,
      EVENT_PATH,
      () => new HttpResponse(null, { status: 404 }),
    );

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
    const { rerender } = renderModal();
    await screen.findByText('Details for 2026test_sf2m1 at 2026test');
    useSearchMock.mockReturnValue({});

    rerender(<MatchModal />);

    expect(
      screen.getByText('Details for 2026test_sf2m1 at 2026test'),
    ).toBeTruthy();
  });
});
