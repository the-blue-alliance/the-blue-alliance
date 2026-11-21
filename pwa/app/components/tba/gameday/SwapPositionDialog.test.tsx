import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { SwapPositionDialog } from '~/components/tba/gameday/SwapPositionDialog';
import { Layout } from '~/lib/gameday/layouts';

const { useGamedayMock } = vi.hoisted(() => ({
  useGamedayMock: vi.fn<() => { state: { layoutId: number | null } }>(),
}));

vi.mock('~/lib/gameday/context', () => ({ useGameday: useGamedayMock }));

function renderDialog(layoutId: number | null) {
  useGamedayMock.mockReturnValue({ state: { layoutId } });
  const onPositionSelected = vi.fn<(position: number) => void>();
  const result = render(
    <SwapPositionDialog
      open
      onOpenChange={() => undefined}
      currentPosition={1}
      onPositionSelected={onPositionSelected}
    />,
  );
  return { ...result, onPositionSelected };
}

describe('SwapPositionDialog', () => {
  test('renders nothing without a layout', () => {
    const { container } = renderDialog(null);

    expect(container.innerHTML).toBe('');
  });

  test('offers every other position in the layout', () => {
    const { onPositionSelected } = renderDialog(Layout.ONE_PLUS_TWO);

    expect(screen.getByText('Select a position to swap with')).toBeTruthy();
    const current = screen.getByRole('button', {
      name: 'Swap with position 2',
    });
    expect((current as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(
      screen.getByRole('button', { name: 'Swap with position 3' }),
    );

    expect(onPositionSelected).toHaveBeenCalledWith(2);
  });
});
