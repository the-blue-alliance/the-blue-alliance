import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { KeyboardShortcutsDialog } from '~/components/tba/moderation/keyboardShortcutsDialog';

describe('KeyboardShortcutsDialog', () => {
  test('lists each shortcut with its key', () => {
    render(<KeyboardShortcutsDialog open onOpenChange={() => undefined} />);

    expect(
      screen.getByRole('heading', { name: 'Keyboard Shortcuts' }),
    ).toBeTruthy();
    const rows = [...document.querySelectorAll('dl > div')].map((row) => [
      row.querySelector('dd')?.textContent,
      row.querySelector('kbd')?.textContent,
    ]);
    expect(rows).toEqual([
      ['Focus the next suggestion', 'j'],
      ['Focus the previous suggestion', 'k'],
      ['Toggle accept on the focused suggestion', 'a'],
      ['Toggle reject on the focused suggestion', 'r'],
      ['Toggle "add as preferred" on the focused image (team media)', 'p'],
      ['Show this dialog', '?'],
    ]);
  });

  test('renders nothing while closed', () => {
    render(
      <KeyboardShortcutsDialog open={false} onOpenChange={() => undefined} />,
    );

    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull();
  });

  test('asks to close from the close button', () => {
    const onOpenChange = vi.fn<(open: boolean) => void>();
    render(<KeyboardShortcutsDialog open onOpenChange={onOpenChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'Close' }));

    expect(onOpenChange).toHaveBeenCalledWith(false, expect.anything());
  });
});
