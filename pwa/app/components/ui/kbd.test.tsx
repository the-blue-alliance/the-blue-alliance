import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Kbd, KbdGroup } from '~/components/ui/kbd';

describe('Kbd', () => {
  test('renders keys inside a group', () => {
    render(
      <KbdGroup className="gap-2" data-testid="group">
        <Kbd className="px-2">Ctrl</Kbd>
        <Kbd>K</Kbd>
      </KbdGroup>,
    );

    const group = screen.getByTestId('group');
    expect(group.getAttribute('data-slot')).toBe('kbd-group');
    expect(group.className).toContain('gap-2');

    const key = screen.getByText('Ctrl');
    expect(key.tagName).toBe('KBD');
    expect(key.getAttribute('data-slot')).toBe('kbd');
    expect(key.className).toContain('px-2');
  });
});
