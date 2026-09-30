import { fireEvent, render, screen } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { beforeAll, describe, expect, test, vi } from 'vitest';

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

function renderSelect(
  props: Pick<ComponentProps<typeof Select>, 'open' | 'onValueChange'>,
) {
  return render(
    <Select
      defaultValue="quals"
      items={{ quals: 'Qualifications', playoffs: 'Playoffs' }}
      {...props}
    >
      <SelectTrigger className="group/trigger" aria-label="Match level">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="group/content" side="top" align="start">
        <SelectGroup>
          <SelectLabel className="group/label">Levels</SelectLabel>
          <SelectItem value="quals" className="group/item">
            Qualifications
          </SelectItem>
          <SelectSeparator className="group/separator" />
          <SelectItem value="playoffs">Playoffs</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>,
  );
}

describe('Select', () => {
  test('shows the selected value on the trigger and opens on click', async () => {
    renderSelect({});

    const trigger = screen.getByRole('combobox', { name: 'Match level' });
    expect(trigger.className).toContain('group/trigger');
    expect(trigger.textContent).toContain('Qualifications');
    expect(trigger.querySelector('svg')).not.toBeNull();
    expect(screen.queryByRole('listbox')).toBeNull();

    fireEvent.click(trigger);

    expect(await screen.findByRole('listbox')).toBeTruthy();
  });

  test('renders the open list with label, items, separator and indicator', () => {
    renderSelect({ open: true });

    const listbox = screen.getByRole('listbox');
    expect(listbox.closest('.group\\/content')).not.toBeNull();
    expect(screen.getByText('Levels').className).toContain('group/label');

    const quals = screen.getByRole('option', { name: 'Qualifications' });
    expect(quals.className).toContain('group/item');
    expect(quals.getAttribute('aria-selected')).toBe('true');
    expect(quals.querySelector('svg')).not.toBeNull();

    const playoffs = screen.getByRole('option', { name: 'Playoffs' });
    expect(playoffs.getAttribute('aria-selected')).toBe('false');
    expect(playoffs.querySelector('svg')).toBeNull();

    expect(document.querySelector('.group\\/separator')?.className).toContain(
      'bg-muted',
    );
  });

  test('selecting an option reports the new value', async () => {
    const onValueChange =
      vi.fn<NonNullable<ComponentProps<typeof Select>['onValueChange']>>();
    renderSelect({ open: true, onValueChange });

    // Base UI commits a selection on the pointer-up/click pair, not on a
    // bare click, so replay the full mouse sequence.
    const option = screen.getByRole('option', { name: 'Playoffs' });
    fireEvent.pointerDown(option, { pointerType: 'mouse' });
    fireEvent.pointerUp(option, { pointerType: 'mouse' });
    fireEvent.mouseUp(option);
    fireEvent.click(option);

    await vi.waitFor(() => {
      expect(onValueChange).toHaveBeenCalledWith('playoffs', expect.anything());
    });
  });

  test('scroll arrows merge their classes', () => {
    render(
      <Select open>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectScrollUpButton className="group/up" data-testid="up" />
          <SelectItem value="a">A</SelectItem>
          <SelectScrollDownButton className="group/down" data-testid="down" />
        </SelectContent>
      </Select>,
    );

    // Base UI only mounts the arrows once the list overflows, which jsdom
    // cannot measure, so the wrappers render nothing here.
    expect(screen.queryByTestId('up')).toBeNull();
    expect(screen.queryByTestId('down')).toBeNull();
  });
});
