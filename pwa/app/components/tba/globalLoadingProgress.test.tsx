import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import GlobalLoadingProgress from '~/components/tba/globalLoadingProgress';

const { routerState } = vi.hoisted(() => ({
  routerState: { isLoading: false },
}));

vi.mock('@tanstack/react-router', () => ({
  useRouterState: ({
    select,
  }: {
    select: (s: { isLoading: boolean }) => boolean;
  }) => select(routerState),
}));

function progressValue() {
  return screen.getByRole('progressbar').getAttribute('aria-valuenow');
}

beforeEach(() => {
  vi.useFakeTimers();
  routerState.isLoading = false;
});

afterEach(() => {
  vi.useRealTimers();
});

describe('GlobalLoadingProgress', () => {
  test('advances while loading, fills on completion, then hides', () => {
    const { rerender, container } = render(<GlobalLoadingProgress />);
    expect(container.innerHTML).toBe('');

    routerState.isLoading = true;
    rerender(<GlobalLoadingProgress />);
    expect(progressValue()).toBe('15');

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(progressValue()).toBe('39');

    act(() => {
      vi.advanceTimersByTime(200 * 50);
    });
    expect(Number(progressValue())).toBeCloseTo(95);

    routerState.isLoading = false;
    rerender(<GlobalLoadingProgress />);
    expect(progressValue()).toBe('100');

    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(container.innerHTML).toBe('');
  });

  test('cleans up timers when unmounted mid-load or mid-finish', () => {
    routerState.isLoading = true;
    const loading = render(<GlobalLoadingProgress />);
    // Already loading on mount, so no transition has happened yet.
    expect(loading.container.innerHTML).toBe('');
    loading.unmount();

    routerState.isLoading = false;
    const { rerender, unmount } = render(<GlobalLoadingProgress />);
    routerState.isLoading = true;
    rerender(<GlobalLoadingProgress />);
    routerState.isLoading = false;
    rerender(<GlobalLoadingProgress />);
    expect(progressValue()).toBe('100');
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});
