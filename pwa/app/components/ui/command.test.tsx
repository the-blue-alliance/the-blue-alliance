import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test, vi } from 'vitest';

import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '~/components/ui/command';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
  // cmdk scrolls the selected item into view, which jsdom does not implement.
  Element.prototype.scrollIntoView = vi.fn<() => void>();
});

function renderPalette(onSelect = vi.fn<(value: string) => void>()) {
  return render(
    <Command className="group/command">
      <CommandInput placeholder="Search" className="group/input" />
      <CommandList className="group/list">
        <CommandEmpty>No results</CommandEmpty>
        <CommandGroup heading="Teams" className="group/group">
          <CommandItem value="254" onSelect={onSelect} className="group/item">
            Team 254
            <CommandShortcut className="group/shortcut">⌘1</CommandShortcut>
          </CommandItem>
          <CommandItem value="1678">Team 1678</CommandItem>
        </CommandGroup>
        <CommandSeparator className="group/separator" />
      </CommandList>
    </Command>,
  );
}

describe('Command', () => {
  test('renders the palette with merged classes and selects items', () => {
    const onSelect = vi.fn<(value: string) => void>();
    renderPalette(onSelect);

    const input = screen.getByPlaceholderText('Search');
    expect(input.getAttribute('data-slot')).toBe('command-input');
    expect(input.className).toContain('group/input');
    const wrapper = input.parentElement;
    expect(wrapper?.getAttribute('data-slot')).toBe('command-input-wrapper');
    expect(wrapper?.querySelector('svg')).not.toBeNull();
    expect(wrapper?.closest('[data-slot="command"]')?.className).toContain(
      'group/command',
    );

    expect(
      document.querySelector('[data-slot="command-list"]')?.className,
    ).toContain('group/list');
    expect(
      document.querySelector('[data-slot="command-group"]')?.className,
    ).toContain('group/group');
    expect(
      document.querySelector('[data-slot="command-separator"]')?.className,
    ).toContain('group/separator');
    expect(screen.getByText('⌘1').className).toContain('group/shortcut');
    expect(screen.queryByText('No results')).toBeNull();

    const item = screen.getByRole('option', { name: /Team 254/ });
    expect(item.className).toContain('group/item');
    fireEvent.click(item);
    expect(onSelect).toHaveBeenCalledWith('254');
  });

  test('shows the empty state when nothing matches the query', async () => {
    renderPalette();

    fireEvent.change(screen.getByPlaceholderText('Search'), {
      target: { value: 'zzz' },
    });

    expect(await screen.findByText('No results')).toBeTruthy();
    expect(screen.queryByRole('option', { name: /Team 254/ })).toBeNull();
  });
});

describe('CommandDialog', () => {
  test('wraps the palette in a dialog with hidden title and description', () => {
    render(
      <CommandDialog open className="group/dialog">
        <CommandList>
          <CommandItem>Only item</CommandItem>
        </CommandList>
      </CommandDialog>,
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog.className).toContain('group/dialog');
    expect(
      screen.getByText('Command Palette').closest('.sr-only'),
    ).not.toBeNull();
    expect(screen.getByText('Search for a command to run...')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Close' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Only item' })).toBeTruthy();
  });

  test('accepts custom copy and can hide the close button', () => {
    render(
      <CommandDialog
        open
        title="Jump to"
        description="Type a team or event"
        showCloseButton={false}
      >
        <CommandList>
          <CommandItem>Only item</CommandItem>
        </CommandList>
      </CommandDialog>,
    );

    expect(screen.getByText('Jump to')).toBeTruthy();
    expect(screen.getByText('Type a team or event')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();
  });
});
