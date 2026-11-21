import { act, renderHook } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { GamedayProvider, useGameday } from '~/lib/gameday/context';
import { Layout } from '~/lib/gameday/layouts';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import type { GamedaySearchParams } from '~/routes/gameday';

const mocks = vi.hoisted(() => ({
  useFirebaseWebcasts:
    vi.fn<
      () => { webcasts: Record<string, WebcastWithMeta>; isLoading: boolean }
    >(),
  useSearch: vi.fn<() => GamedaySearchParams>(),
  navigate: vi.fn<() => Promise<void>>(),
}));

vi.mock('~/lib/gameday/useFirebaseWebcasts', () => ({
  useFirebaseWebcasts: mocks.useFirebaseWebcasts,
}));

vi.mock('@tanstack/react-router', () => ({
  useSearch: mocks.useSearch,
  useNavigate: () => mocks.navigate,
}));

vi.mock('~/components/tba/gameday/MatchRecommendationsPanel', () => ({
  MatchRecommendationsPanel: () => null,
}));

function webcast(id: string, name: string, isSpecial = false): WebcastWithMeta {
  return { id, name, isSpecial, webcast: { type: 'twitch', channel: name } };
}

const WEBCASTS: Record<string, WebcastWithMeta> = {
  '2024casj-0': webcast('2024casj-0', 'Silicon Valley 1'),
  '2024casj-1': webcast('2024casj-1', 'Silicon Valley 2'),
  '2024mil-0': webcast('2024mil-0', 'Milstein'),
  'frn-0': webcast('frn-0', 'FRN', true),
};

const PANEL_ID = 'data-panel:match-recommendations';

function renderGameday(initialEventCode?: string) {
  return renderHook(() => useGameday(), {
    wrapper: ({ children }: PropsWithChildren) => (
      <GamedayProvider initialEventCode={initialEventCode}>
        {children}
      </GamedayProvider>
    ),
  });
}

describe('useGameday', () => {
  beforeEach(() => {
    mocks.useSearch.mockReturnValue({});
    mocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: WEBCASTS,
      isLoading: false,
    });
  });

  test('throws outside a GamedayProvider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => renderHook(() => useGameday())).toThrow(
      'useGameday must be used within a GamedayProvider',
    );
  });

  test('offers every webcast and data panel as content', () => {
    const { result } = renderGameday();

    expect(Object.keys(result.current.contentById).sort()).toEqual([
      '2024casj-0',
      '2024casj-1',
      '2024mil-0',
      PANEL_ID,
      'frn-0',
    ]);
  });

  test('is not initializing without url state or an event code', () => {
    const { result } = renderGameday();

    expect(result.current.isInitializing).toBe(false);
  });

  test('is initializing while Firebase loads webcasts for an event code', () => {
    mocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: {},
      isLoading: true,
    });

    const { result } = renderGameday('2024casj');

    expect(result.current.isInitializing).toBe(true);
  });

  test('is initializing until url state is restored', () => {
    mocks.useSearch.mockReturnValue({ layout: 1 });
    mocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: {},
      isLoading: true,
    });

    const { result } = renderGameday();

    expect(result.current.isInitializing).toBe(true);
  });

  test('restores the layout and views from the url once webcasts load', () => {
    mocks.useSearch.mockReturnValue({ layout: 1, view_0: '2024mil-0' });

    const { result } = renderGameday();

    expect(result.current.isInitializing).toBe(false);
    expect(result.current.state).toMatchObject({
      layoutId: 1,
      positionToContent: [
        '2024mil-0',
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
      ],
    });
  });

  test('auto-loads the webcasts of the initial event into a fitting layout', () => {
    const { result } = renderGameday('2024casj');

    expect(result.current.state.layoutId).toBe(Layout.VERTICAL_SPLIT);
    expect(result.current.state.positionToContent.slice(0, 3)).toEqual([
      '2024casj-0',
      '2024casj-1',
      null,
    ]);
  });

  test('does not auto-load the event when the url already carries state', () => {
    mocks.useSearch.mockReturnValue({ layout: 0 });

    const { result } = renderGameday('2024casj');

    expect(result.current.state.positionToContent[0]).toBeNull();
  });

  test('leaves the layout alone for an event without webcasts', () => {
    const { result } = renderGameday('2024none');

    expect(result.current.state.layoutId).toBeNull();
  });

  test('lists content that is not currently displayed as available', () => {
    const { result } = renderGameday('2024casj');

    expect(result.current.availableContent.map((c) => c.id).sort()).toEqual([
      '2024mil-0',
      PANEL_ID,
      'frn-0',
    ]);
  });

  test('setLayout switches the layout', () => {
    const { result } = renderGameday();

    act(() => result.current.setLayout(Layout.VERTICAL_SPLIT));

    expect(result.current.state.layoutId).toBe(Layout.VERTICAL_SPLIT);
  });

  test('addContentAtPosition places content in a view', () => {
    const { result } = renderGameday();
    act(() => result.current.setLayout(Layout.VERTICAL_SPLIT));

    act(() => result.current.addContentAtPosition('2024mil-0', 1));

    expect(result.current.state.positionToContent[1]).toBe('2024mil-0');
  });

  test('removeContent clears the view showing that content', () => {
    const { result } = renderGameday('2024casj');

    act(() => result.current.removeContent('2024casj-0'));

    expect(result.current.state.positionToContent.slice(0, 2)).toEqual([
      null,
      '2024casj-1',
    ]);
  });

  test('swapPositions exchanges two views', () => {
    const { result } = renderGameday('2024casj');

    act(() => result.current.swapPositions(0, 1));

    expect(result.current.state.positionToContent.slice(0, 2)).toEqual([
      '2024casj-1',
      '2024casj-0',
    ]);
  });

  test('resetContent empties every view', () => {
    const { result } = renderGameday('2024casj');

    act(() => result.current.resetContent());

    expect(
      result.current.state.positionToContent.every((id) => id === null),
    ).toBe(true);
  });

  test('toggleChatSidebar hides the chat', () => {
    const { result } = renderGameday();

    act(() => result.current.toggleChatSidebar());

    expect(result.current.state.chatSidebarVisible).toBe(false);
  });

  test('setCurrentChat switches the chat channel', () => {
    const { result } = renderGameday();

    act(() => result.current.setCurrentChat('tbagameday'));

    expect(result.current.state.currentChat).toBe('tbagameday');
  });
});
