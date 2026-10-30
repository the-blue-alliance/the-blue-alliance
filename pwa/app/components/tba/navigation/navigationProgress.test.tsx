import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { NavigationProgress } from '~/components/tba/navigation/navigationProgress';

const router = vi.hoisted(() => ({ state: { isLoading: false } }));

vi.mock('@tanstack/react-router', () => ({
  useRouterState: <T,>({
    select,
  }: {
    select: (state: typeof router.state) => T;
  }) => select(router.state),
}));

describe('NavigationProgress', () => {
  test('shows a page loading progress bar while a navigation is loading', () => {
    router.state = { isLoading: true };

    render(<NavigationProgress />);

    expect(
      screen.getByRole('progressbar', { name: 'Loading page' }),
    ).toBeTruthy();
  });

  test('shows no progress bar when no navigation is loading', () => {
    router.state = { isLoading: false };

    render(<NavigationProgress />);

    expect(screen.queryByRole('progressbar')).toBeNull();
  });
});
