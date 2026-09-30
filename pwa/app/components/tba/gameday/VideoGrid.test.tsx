import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { VideoGrid } from '~/components/tba/gameday/VideoGrid';
import { Layout, getLayoutById } from '~/lib/gameday/layouts';
import type { GamedayContent } from '~/lib/gameday/types';

const { useGamedayMock } = vi.hoisted(() => ({
  useGamedayMock: vi.fn<
    () => {
      state: { layoutId: number | null; positionToContent: (string | null)[] };
      contentById: Record<string, GamedayContent>;
    }
  >(),
}));

vi.mock('~/lib/gameday/context', () => ({ useGameday: useGamedayMock }));
vi.mock('~/components/tba/gameday/VideoCell', () => ({
  VideoCell: ({
    position,
    content,
    gridArea,
  }: {
    position: number;
    content: GamedayContent | null;
    gridArea: string;
  }) => (
    <div data-testid="cell">
      {`${position}:${gridArea}:${content?.name ?? 'empty'}`}
    </div>
  ),
}));

const PANEL: GamedayContent = {
  type: 'data-panel',
  id: 'data-panel:b',
  name: 'Panel B',
  component: () => null,
};

describe('VideoGrid', () => {
  test('renders nothing without a layout', () => {
    useGamedayMock.mockReturnValue({
      state: { layoutId: null, positionToContent: [] },
      contentById: {},
    });

    const { container } = render(<VideoGrid />);

    expect(container.innerHTML).toBe('');
  });

  test('orders filled cells by content id, then empty cells by position', () => {
    useGamedayMock.mockReturnValue({
      state: {
        layoutId: Layout.QUAD_VIEW,
        positionToContent: [null, 'data-panel:b', null, 'data-panel:a'],
      },
      contentById: { 'data-panel:b': PANEL },
    });

    const { container } = render(<VideoGrid />);

    expect(
      screen.getAllByTestId('cell').map((cell) => cell.textContent),
    ).toEqual(['3:d:empty', '1:b:Panel B', '0:a:empty', '2:c:empty']);
    expect(
      (container.firstElementChild as HTMLElement).style.gridTemplate,
    ).toBe(getLayoutById(Layout.QUAD_VIEW)?.gridTemplate);
  });
});
