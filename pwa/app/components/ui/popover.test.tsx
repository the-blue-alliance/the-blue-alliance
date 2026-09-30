import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test } from 'vitest';

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

describe('Popover', () => {
  test('opens its content when the trigger is clicked', async () => {
    render(
      <Popover>
        <PopoverTrigger>Show details</PopoverTrigger>
        <PopoverContent className="group/content" side="top" align="start">
          Popover body
        </PopoverContent>
      </Popover>,
    );

    const trigger = screen.getByRole('button', { name: 'Show details' });
    expect(trigger.getAttribute('data-slot')).toBe('popover-trigger');
    expect(screen.queryByText('Popover body')).toBeNull();

    fireEvent.click(trigger);

    const body = await screen.findByText('Popover body');
    expect(body.getAttribute('data-slot')).toBe('popover-content');
    expect(body.className).toContain('group/content');
  });

  test('renders open content with default alignment', () => {
    render(
      <Popover open>
        <PopoverTrigger>Show</PopoverTrigger>
        <PopoverContent>Already open</PopoverContent>
      </Popover>,
    );

    expect(screen.getByText('Already open')).toBeTruthy();
  });
});
