import { render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test } from 'vitest';

import { ScrollArea, ScrollBar } from '~/components/ui/scroll-area';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

describe('ScrollArea', () => {
  test('renders children inside the viewport', () => {
    render(
      <ScrollArea className="h-20" data-testid="root">
        <p>Scrollable content</p>
      </ScrollArea>,
    );

    const root = screen.getByTestId('root');
    expect(root.getAttribute('data-slot')).toBe('scroll-area');
    expect(root.className).toContain('h-20');
    expect(
      screen
        .getByText('Scrollable content')
        .closest('[data-slot="scroll-area-viewport"]'),
    ).toBeTruthy();
  });

  test('renders a horizontal scrollbar', () => {
    const { container } = render(
      <ScrollArea>
        <p>Wide content</p>
        <ScrollBar orientation="horizontal" keepMounted className="mt-2" />
      </ScrollArea>,
    );

    const horizontal = container.querySelector(
      '[data-slot="scroll-area-scrollbar"][data-orientation="horizontal"]',
    );
    expect(horizontal).toBeTruthy();
    expect(horizontal?.className).toContain('flex-col');
    expect(horizontal?.className).toContain('mt-2');
  });
});
