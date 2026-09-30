import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { GamedayFrame } from '~/components/tba/gameday/GamedayFrame';

const { useGamedayMock } = vi.hoisted(() => ({
  useGamedayMock:
    vi.fn<
      () => { state: { layoutId: number | null }; isInitializing: boolean }
    >(),
}));

vi.mock('~/lib/gameday/context', () => ({ useGameday: useGamedayMock }));
vi.mock('~/components/tba/gameday/ChatSidebar', () => ({
  ChatSidebar: () => <aside>Chat sidebar</aside>,
}));
vi.mock('~/components/tba/gameday/GamedayToolbar', () => ({
  GamedayToolbar: () => <header>Toolbar</header>,
}));
vi.mock('~/components/tba/gameday/LayoutSelector', () => ({
  LayoutSelector: () => <div>Layout selector</div>,
}));
vi.mock('~/components/tba/gameday/VideoGrid', () => ({
  VideoGrid: () => <div>Video grid</div>,
}));

function renderFrame(layoutId: number | null, isInitializing = false) {
  useGamedayMock.mockReturnValue({ state: { layoutId }, isInitializing });
  render(<GamedayFrame />);
}

describe('GamedayFrame', () => {
  test('shows only the toolbar while restoring URL state', () => {
    renderFrame(null, true);

    expect(screen.getByText('Toolbar')).toBeTruthy();
    expect(screen.queryByText('Layout selector')).toBeNull();
    expect(screen.queryByText('Video grid')).toBeNull();
  });

  test('asks for a layout when none is chosen', () => {
    renderFrame(null);

    expect(screen.getByText('Layout selector')).toBeTruthy();
    expect(screen.queryByText('Chat sidebar')).toBeNull();
  });

  test('shows the video grid and chat once a layout is chosen', () => {
    renderFrame(3);

    expect(screen.getByText('Video grid')).toBeTruthy();
    expect(screen.getByText('Chat sidebar')).toBeTruthy();
  });
});
