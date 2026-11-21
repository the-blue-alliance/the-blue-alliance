import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test } from 'vitest';

import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuIndicator,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  NavigationMenuViewport,
} from '~/components/ui/navigation-menu';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

function renderMenu(value?: string) {
  return render(
    <NavigationMenu value={value} className="group/menu" data-testid="menu">
      <NavigationMenuList className="group/list">
        <NavigationMenuItem value="events" className="group/item">
          <NavigationMenuTrigger className="group/trigger">
            Events
            <NavigationMenuIndicator className="group/indicator" />
          </NavigationMenuTrigger>
          <NavigationMenuContent className="group/content">
            <NavigationMenuLink href="/events" className="group/link">
              All events
            </NavigationMenuLink>
          </NavigationMenuContent>
        </NavigationMenuItem>
      </NavigationMenuList>
      <NavigationMenuViewport className="group/viewport" />
    </NavigationMenu>,
  );
}

describe('NavigationMenu', () => {
  test('renders the closed menu with merged classes', () => {
    renderMenu();

    const menu = screen.getByTestId('menu');
    expect(menu.getAttribute('data-slot')).toBe('navigation-menu');
    expect(menu.className).toContain('group/menu');
    expect(
      menu.querySelector('[data-slot="navigation-menu-list"]')?.className,
    ).toContain('group/list');
    expect(
      menu.querySelector('[data-slot="navigation-menu-item"]')?.className,
    ).toContain('group/item');

    const trigger = screen.getByRole('button', { name: 'Events' });
    expect(trigger.className).toContain('group/trigger');
    const indicator = trigger.querySelector(
      '[data-slot="navigation-menu-indicator"]',
    );
    expect(indicator?.className).toContain('group/indicator');
    expect(indicator?.querySelector('div')).not.toBeNull();

    expect(screen.queryByRole('link', { name: 'All events' })).toBeNull();
  });

  test('shows the active item content in the viewport', () => {
    renderMenu('events');

    const link = screen.getByRole('link', { name: 'All events' });
    expect(link.getAttribute('href')).toBe('/events');
    expect(link.getAttribute('data-slot')).toBe('navigation-menu-link');
    expect(link.className).toContain('group/link');

    const content = link.closest('[data-slot="navigation-menu-content"]');
    expect(content?.className).toContain('group/content');
    expect(
      document.querySelector('[data-slot="navigation-menu-viewport"]')
        ?.className,
    ).toContain('group/viewport');
  });

  test('opens when the trigger is clicked', async () => {
    renderMenu();

    fireEvent.click(screen.getByRole('button', { name: 'Events' }));

    expect(
      await screen.findByRole('link', { name: 'All events' }),
    ).toBeTruthy();
  });
});
