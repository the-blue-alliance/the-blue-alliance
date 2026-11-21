import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { NotificationType } from '~/api/tba/mobile/types.gen';
import PreferencesDialog from '~/components/tba/preferencesDialog';

const { myTBA } = vi.hoisted(() => ({
  myTBA: {
    isFavorite: false,
    notifications: [] as NotificationType[],
    isPending: false,
    setPreferences:
      vi.fn<(favorite: boolean, notifications: NotificationType[]) => void>(),
  },
}));

vi.mock('~/lib/hooks', () => ({ useMediaQuery: () => true }));

vi.mock('~/lib/hooks/useMyTBA', () => ({
  useMyTBA: () => ({ ...myTBA, toggleFavorite: () => {} }),
}));

beforeEach(() => {
  myTBA.isFavorite = false;
  myTBA.notifications = ['match_score'];
  myTBA.isPending = false;
});

function checkbox(name: string) {
  return screen.getByRole('checkbox', { name });
}

describe('PreferencesDialog', () => {
  test('saves edited preferences from an uncontrolled dialog', async () => {
    render(
      <PreferencesDialog
        modelKey="frc254"
        modelType={1}
        trigger={<button>Prefs</button>}
      />,
    );
    expect(screen.queryByText('Preferences for frc254')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Prefs' }));
    expect(await screen.findByText('Preferences for frc254')).toBeTruthy();
    expect(checkbox('Favorite').getAttribute('aria-checked')).toBe('false');
    expect(checkbox('Match Score').getAttribute('aria-checked')).toBe('true');

    fireEvent.click(checkbox('Favorite'));
    fireEvent.click(checkbox('Match Score'));
    fireEvent.click(checkbox('Upcoming Match'));
    expect(checkbox('Favorite').getAttribute('aria-checked')).toBe('true');

    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(myTBA.setPreferences).toHaveBeenCalledWith(true, ['upcoming_match']);
    await vi.waitFor(() =>
      expect(screen.queryByText('Preferences for frc254')).toBeNull(),
    );
  });

  test('unchecks favorite', async () => {
    myTBA.isFavorite = true;
    render(
      <PreferencesDialog
        modelKey="frc254"
        modelType={1}
        trigger={<button>Prefs</button>}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Prefs' }));
    await screen.findByText('Preferences for frc254');
    fireEvent.click(checkbox('Favorite'));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(myTBA.setPreferences).toHaveBeenCalledWith(false, ['match_score']);
  });

  test('reports close requests from a controlled dialog', async () => {
    myTBA.isPending = true;
    const onOpenChange = vi.fn<(open: boolean, details?: unknown) => void>();
    render(
      <PreferencesDialog
        modelKey="2026miket"
        modelType={0}
        trigger={<button>Prefs</button>}
        open
        onOpenChange={onOpenChange}
      />,
    );
    expect(await screen.findByText('Preferences for 2026miket')).toBeTruthy();
    const save = screen.getByRole('button', { name: 'Save' });
    expect(save.hasAttribute('disabled')).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onOpenChange).toHaveBeenCalledWith(false, expect.anything());
    // Still open until the parent says otherwise.
    expect(screen.getByText('Preferences for 2026miket')).toBeTruthy();
  });

  test('closes via the form without an onOpenChange handler', async () => {
    render(
      <PreferencesDialog
        modelKey="2026miket"
        modelType={0}
        trigger={<button>Prefs</button>}
        open
      />,
    );
    await screen.findByText('Preferences for 2026miket');
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(myTBA.setPreferences).toHaveBeenCalledWith(false, ['match_score']);
  });
});
