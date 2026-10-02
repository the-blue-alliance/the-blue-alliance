import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { WebcastStatus } from '~/api/tba/read';
import { WebcastSelectorDialog } from '~/components/tba/gameday/WebcastSelectorDialog';
import type { FirebaseWebcast, GamedayContent } from '~/lib/gameday/types';

const { useGamedayMock } = vi.hoisted(() => ({
  useGamedayMock: vi.fn<() => { availableContent: GamedayContent[] }>(),
}));

vi.mock('~/lib/gameday/context', () => ({
  useGameday: useGamedayMock,
}));

const availableContent: GamedayContent[] = [
  {
    type: 'data-panel',
    id: 'data-panel:match-recommendations',
    name: 'Match Recommendations',
    component: () => null,
  },
  {
    type: 'webcast',
    id: '2026miket-0',
    name: 'Kettering #1',
    webcast: {
      id: '2026miket-0',
      name: 'Kettering #1',
      webcast: { type: 'youtube', channel: 'tba' },
      isSpecial: false,
    },
  },
];

describe('WebcastSelectorDialog', () => {
  beforeEach(() => {
    useGamedayMock.mockReturnValue({ availableContent });
  });

  test('lists data panels alongside webcasts', () => {
    render(
      <WebcastSelectorDialog
        open
        onOpenChange={() => undefined}
        onContentSelected={() => undefined}
      />,
    );

    expect(
      screen
        .getAllByRole('button')
        .map((button) => button.textContent?.trim())
        .filter(Boolean),
    ).toEqual(['Match Recommendations', 'Kettering #1', 'Close']);
  });

  test('selects a data panel by its content id', () => {
    const onContentSelected = vi.fn<(contentId: string) => void>();
    render(
      <WebcastSelectorDialog
        open
        onOpenChange={() => undefined}
        onContentSelected={onContentSelected}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: 'Match Recommendations' }),
    );

    expect(onContentSelected).toHaveBeenCalledWith(
      'data-panel:match-recommendations',
    );
  });

  test('omits a data panel that is already in the grid', () => {
    useGamedayMock.mockReturnValue({
      availableContent: availableContent.filter(
        (content) => content.type === 'webcast',
      ),
    });

    render(
      <WebcastSelectorDialog
        open
        onOpenChange={() => undefined}
        onContentSelected={() => undefined}
      />,
    );

    expect(
      screen.queryByRole('button', { name: 'Match Recommendations' }),
    ).toBeNull();
  });
});

function webcastContent(
  id: string,
  isSpecial: boolean,
  webcast: FirebaseWebcast,
): GamedayContent {
  return {
    type: 'webcast',
    id,
    name: id,
    webcast: { id, name: id, webcast, isSpecial },
  };
}

function renderWithContent(
  content: GamedayContent[],
  onContentSelected: (contentId: string) => void = () => undefined,
) {
  useGamedayMock.mockReturnValue({ availableContent: content });
  render(
    <WebcastSelectorDialog
      open
      onOpenChange={() => undefined}
      onContentSelected={onContentSelected}
    />,
  );
}

function sectionHeadings() {
  return screen
    .getAllByText(/Webcasts$|^Data Panels$/)
    .map((heading) => heading.textContent);
}

describe('WebcastSelectorDialog grouping', () => {
  test('says when nothing is available', () => {
    renderWithContent([]);

    expect(screen.getByText('No content available')).toBeTruthy();
  });

  test('groups webcasts by kind and online status', () => {
    renderWithContent([
      webcastContent('Special live', true, {
        type: 'twitch',
        channel: 'a',
        status: WebcastStatus.ONLINE,
        stream_title: 'Einstein Finals',
        viewer_count: 12345,
      }),
      webcastContent('Special offline', true, {
        type: 'twitch',
        channel: 'b',
        status: WebcastStatus.OFFLINE,
      }),
      webcastContent('Event live', false, {
        type: 'youtube',
        channel: 'c',
        status: WebcastStatus.ONLINE,
      }),
      webcastContent('Event offline', false, {
        type: 'youtube',
        channel: 'd',
        status: WebcastStatus.OFFLINE,
      }),
    ]);

    expect(sectionHeadings()).toEqual([
      'Special Webcasts',
      'Event Webcasts',
      'Offline Event Webcasts',
      'Offline Special Webcasts',
    ]);
    const live = screen.getByRole('button', { name: /Special live/ });
    expect(live.textContent).toContain('Einstein Finals');
    expect(live.textContent).toContain(`${(12345).toLocaleString()}Viewers`);
    // Online without a title or viewer count shows only the name.
    expect(screen.getByRole('button', { name: /Event live/ }).textContent).toBe(
      'Event live',
    );
  });

  test('selects a webcast from any section by its content id', () => {
    const onContentSelected = vi.fn<(contentId: string) => void>();
    const ids = ['special-on', 'special-off', 'event-on', 'event-off'];
    renderWithContent(
      ids.map((id) =>
        webcastContent(id, id.startsWith('special'), {
          type: 'twitch',
          channel: id,
          status: id.endsWith('off')
            ? WebcastStatus.OFFLINE
            : WebcastStatus.ONLINE,
        }),
      ),
      onContentSelected,
    );

    for (const id of ids) {
      fireEvent.click(screen.getByRole('button', { name: id }));
    }

    expect(onContentSelected.mock.calls.map(([id]) => id)).toEqual(ids);
  });

  test('shows offline sections on their own', () => {
    renderWithContent([
      webcastContent('Special offline', true, {
        type: 'twitch',
        channel: 'b',
        status: WebcastStatus.OFFLINE,
      }),
    ]);

    expect(sectionHeadings()).toEqual(['Offline Special Webcasts']);
    expect(document.querySelector('[data-slot="separator"]')).toBeNull();
  });

  test('treats unknown status as online and hides its title', () => {
    renderWithContent([
      webcastContent('Unknown', false, {
        type: 'livestream',
        channel: 'e',
        stream_title: 'Hidden title',
      }),
    ]);

    expect(sectionHeadings()).toEqual(['Event Webcasts']);
    expect(screen.queryByText('Hidden title')).toBeNull();
  });
});
