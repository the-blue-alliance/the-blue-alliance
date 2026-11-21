import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test, vi } from 'vitest';

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

describe('DropdownMenu', () => {
  test('opens from its trigger and fires item clicks', async () => {
    const onClick = vi.fn<() => void>();

    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Account</DropdownMenuTrigger>
        <DropdownMenuContent className="group/content">
          <DropdownMenuItem onClick={onClick}>Profile</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(screen.queryByRole('menu')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Account' }));

    const menu = await screen.findByRole('menu');
    expect(menu.className).toContain('group/content');

    fireEvent.click(screen.getByRole('menuitem', { name: 'Profile' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  test('renders every item kind with inset and merged classes', () => {
    render(
      <DropdownMenu open>
        <DropdownMenuTrigger>Account</DropdownMenuTrigger>
        <DropdownMenuPortal>
          <DropdownMenuContent>
            <DropdownMenuGroup>
              <DropdownMenuLabel inset className="group/label">
                Section
              </DropdownMenuLabel>
              <DropdownMenuItem inset className="group/item">
                Profile
                <DropdownMenuShortcut className="group/shortcut">
                  ⌘P
                </DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>Plain</DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator className="group/separator" />
            <DropdownMenuCheckboxItem checked className="group/checkbox">
              Show grid
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={false}>
              Show labels
            </DropdownMenuCheckboxItem>
            <DropdownMenuRadioGroup value="a">
              <DropdownMenuRadioItem value="a" className="group/radio">
                Option A
              </DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="b">Option B</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenuPortal>
      </DropdownMenu>,
    );

    const label = screen.getByText('Section');
    expect(label.className).toContain('group/label');
    expect(label.className).toContain('pl-8');

    const profile = screen.getByRole('menuitem', { name: /Profile/ });
    expect(profile.className).toContain('group/item');
    expect(profile.className).toContain('pl-8');
    expect(
      screen.getByRole('menuitem', { name: 'Plain' }).className,
    ).not.toContain('pl-8');
    expect(screen.getByText('⌘P').className).toContain('group/shortcut');

    expect(screen.getByRole('separator').className).toContain(
      'group/separator',
    );

    const checked = screen.getByRole('menuitemcheckbox', { name: 'Show grid' });
    expect(checked.getAttribute('aria-checked')).toBe('true');
    expect(checked.className).toContain('group/checkbox');
    expect(checked.querySelector('svg')).not.toBeNull();
    const unchecked = screen.getByRole('menuitemcheckbox', {
      name: 'Show labels',
    });
    expect(unchecked.getAttribute('aria-checked')).toBe('false');
    expect(unchecked.querySelector('svg')).toBeNull();

    const radioA = screen.getByRole('menuitemradio', { name: 'Option A' });
    expect(radioA.getAttribute('aria-checked')).toBe('true');
    expect(radioA.className).toContain('group/radio');
    expect(radioA.querySelector('svg')).not.toBeNull();
    expect(
      screen
        .getByRole('menuitemradio', { name: 'Option B' })
        .querySelector('svg'),
    ).toBeNull();
  });

  test('renders an open submenu with its trigger chevron', () => {
    render(
      <DropdownMenu open>
        <DropdownMenuTrigger>Account</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuSub open>
            <DropdownMenuSubTrigger inset className="group/sub-trigger">
              More
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent className="group/sub-content">
              <DropdownMenuItem>Nested</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>Closed</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem>Hidden</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    const subTrigger = screen.getByRole('menuitem', { name: 'More' });
    expect(subTrigger.className).toContain('group/sub-trigger');
    expect(subTrigger.className).toContain('pl-8');
    expect(subTrigger.querySelector('svg')).not.toBeNull();

    const nested = screen.getByRole('menuitem', { name: 'Nested' });
    const subMenu = nested.closest('[role="menu"]');
    expect(subMenu?.className).toContain('group/sub-content');
    expect(subMenu?.className).toContain('w-auto');

    expect(
      screen.getByRole('menuitem', { name: 'Closed' }).className,
    ).not.toContain('pl-8');
    expect(screen.queryByRole('menuitem', { name: 'Hidden' })).toBeNull();
  });
});
