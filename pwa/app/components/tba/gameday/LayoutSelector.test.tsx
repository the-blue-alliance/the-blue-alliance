import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { LayoutSelector } from '~/components/tba/gameday/LayoutSelector';
import { LAYOUT_DISPLAY_ORDER, Layout } from '~/lib/gameday/layouts';

const { setLayout } = vi.hoisted(() => ({
  setLayout: vi.fn<(layoutId: number) => void>(),
}));

vi.mock('~/lib/gameday/context', () => ({
  useGameday: () => ({ setLayout }),
}));

describe('LayoutSelector', () => {
  test('lists every layout in display order', () => {
    render(<LayoutSelector />);

    expect(screen.getByText('Select a layout')).toBeTruthy();
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(LAYOUT_DISPLAY_ORDER.length);
    expect(buttons[0].textContent).toBe('Single View');
    expect(buttons[2].textContent).toBe('Horizontal Split');
  });

  test('chooses the clicked layout', () => {
    render(<LayoutSelector />);

    fireEvent.click(screen.getByRole('button', { name: 'Quad View' }));

    expect(setLayout).toHaveBeenCalledWith(Layout.QUAD_VIEW);
  });
});
