import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { EventCoprs } from '~/api/tba/read';
import { ComponentOprsTable } from '~/components/tba/componentOprsTable';

const { useMediaQueryMock } = vi.hoisted(() => ({
  useMediaQueryMock: vi.fn<(query: string) => boolean>(),
}));

vi.mock('~/lib/hooks', () => ({ useMediaQuery: useMediaQueryMock }));

vi.mock('~/components/tba/teamTooltip', () => ({
  TeamLinkWithTooltip: ({ teamKey }: { teamKey: string }) => (
    <a href={`/team/${teamKey}`}>{teamKey}</a>
  ),
}));

const coprs: EventCoprs = {
  totalPoints: { frc254: 50.123, frc604: 70 },
  autoPoints: { frc254: 10, frc604: 12 },
  teleopPoints: { frc254: 40 },
  endgamePoints: { frc254: 5, frc604: 6 },
  unused: { frc254: 0, frc604: 0 },
};

function headers() {
  return screen.getAllByRole('columnheader').map((h) => h.textContent);
}

describe('ComponentOprsTable', () => {
  beforeEach(() => {
    useMediaQueryMock.mockReturnValue(true);
  });

  test('shows the preferred components on desktop, sorted by total', () => {
    render(<ComponentOprsTable coprs={coprs} year={2025} />);
    expect(headers()).toEqual([
      '#',
      'Team',
      'Total Points ↓',
      'Auto Points',
      'Teleop Points',
    ]);
    const rows = screen.getAllByRole('row').slice(1);
    expect(
      within(rows[0])
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['1', 'frc604', '70.00', '12.00', '—']);
    expect(
      within(rows[1])
        .getAllByRole('cell')
        .map((c) => c.textContent),
    ).toEqual(['2', 'frc254', '50.12', '10.00', '40.00']);
  });

  test('ranks teams by the selected component', () => {
    render(<ComponentOprsTable coprs={coprs} year={2025} />);

    fireEvent.click(screen.getByRole('button', { name: 'Teleop Points' }));

    expect(
      within(screen.getAllByRole('row')[1]).getAllByRole('cell')[0].textContent,
    ).toBe('1');
    expect(
      within(screen.getAllByRole('row')[1]).getByRole('link').textContent,
    ).toBe('frc254');
  });

  test('inverts ranks when the component is sorted ascending', () => {
    render(<ComponentOprsTable coprs={coprs} year={2025} />);

    fireEvent.click(screen.getByRole('button', { name: 'Total Points ↓' }));

    expect(
      screen
        .getAllByRole('row')
        .slice(1)
        .map((row) => within(row).getAllByRole('cell')[0].textContent),
    ).toEqual(['2', '1']);
  });

  test('returns to descending sorting instead of clearing the sort', () => {
    render(<ComponentOprsTable coprs={coprs} year={2025} />);
    fireEvent.click(screen.getByRole('button', { name: 'Total Points ↓' }));

    fireEvent.click(screen.getByRole('button', { name: 'Total Points ↑' }));

    expect(screen.getByRole('button', { name: 'Total Points ↓' })).toBeTruthy();
    expect(
      within(screen.getAllByRole('row')[1]).getByRole('link').textContent,
    ).toBe('frc604');
  });

  test('shows only the sort component on mobile and lets the user pick', async () => {
    useMediaQueryMock.mockReturnValue(false);
    render(<ComponentOprsTable coprs={coprs} year={2025} />);
    expect(headers()).toEqual(['#', 'Team', 'Total Points ↓']);

    fireEvent.click(screen.getByRole('button', { name: 'Columns' }));
    fireEvent.click(
      await screen.findByRole('menuitemcheckbox', { name: 'Endgame Points' }),
    );
    expect(headers()).toEqual([
      '#',
      'Team',
      'Total Points ↓',
      'Endgame Points',
    ]);
  });

  test('does not sort without components', () => {
    render(<ComponentOprsTable coprs={{}} year={2025} />);
    expect(headers()).toEqual(['#', 'Team']);
    expect(screen.getByText('No results.')).toBeTruthy();
  });
});
