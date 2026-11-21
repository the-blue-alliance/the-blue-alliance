import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test } from 'vitest';

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

describe('Tooltip', () => {
  test('shows content when opened', () => {
    render(
      <TooltipProvider>
        <Tooltip open>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent
            className="mt-2"
            viewportClassName="viewport-extra"
            side="bottom"
          >
            Helpful hint
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>,
    );

    expect(screen.getByText('Hover me').getAttribute('data-slot')).toBe(
      'tooltip-trigger',
    );
    const viewport = screen.getByText('Helpful hint');
    expect(viewport.className).toContain('viewport-extra');
    const popup = viewport.closest('[data-slot="tooltip-content"]');
    expect(popup?.className).toContain('mt-2');
  });

  test('opens on focus with the default delay', async () => {
    render(
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>Focus me</TooltipTrigger>
          <TooltipContent>Focused hint</TooltipContent>
        </Tooltip>
      </TooltipProvider>,
    );

    expect(screen.queryByText('Focused hint')).toBeNull();
    fireEvent.focus(screen.getByText('Focus me'));
    expect(await screen.findByText('Focused hint')).toBeTruthy();
  });
});
