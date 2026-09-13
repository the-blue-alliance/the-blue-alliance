import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { WebcastSelectorDialog } from '~/components/tba/gameday/WebcastSelectorDialog';
import type { GamedayContent } from '~/lib/gameday/types';

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
