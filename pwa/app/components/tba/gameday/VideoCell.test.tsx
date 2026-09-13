import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { VideoCell } from '~/components/tba/gameday/VideoCell';
import type { GamedayContent } from '~/lib/gameday/types';

const gamedayMocks = vi.hoisted(() => ({
  addContentAtPosition: vi.fn<(contentId: string, position: number) => void>(),
  removeContent: vi.fn<(contentId: string) => void>(),
  swapPositions: vi.fn<(position1: number, position2: number) => void>(),
}));

vi.mock('~/lib/gameday/context', () => ({
  useGameday: () => ({
    state: { layoutId: 3 },
    availableContent: [],
    ...gamedayMocks,
  }),
}));

const dataPanel: GamedayContent = {
  type: 'data-panel',
  id: 'data-panel:match-recommendations',
  name: 'Match Recommendations',
  component: () => <p>Recommended match contents</p>,
};

describe('VideoCell data panels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders a data panel as grid content', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    expect(screen.getByText('Recommended match contents').textContent).toBe(
      'Recommended match contents',
    );
  });

  test('labels a data panel in the cell toolbar', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    expect(screen.getByText('Match Recommendations').textContent).toBe(
      'Match Recommendations',
    );
  });

  test('removes a data panel through the standard cell control', () => {
    render(<VideoCell position={0} content={dataPanel} gridArea="a" />);

    fireEvent.click(screen.getByRole('button', { name: 'Remove content' }));

    expect(gamedayMocks.removeContent).toHaveBeenCalledWith(
      'data-panel:match-recommendations',
    );
  });
});
