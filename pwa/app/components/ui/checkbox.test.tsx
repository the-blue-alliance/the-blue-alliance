import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { Checkbox } from '~/components/ui/checkbox';

describe('Checkbox', () => {
  test('toggles and reports the change', () => {
    const onCheckedChange = vi.fn<(checked: boolean) => void>();
    render(
      <Checkbox
        aria-label="Accept"
        className="mt-2"
        onCheckedChange={onCheckedChange}
      />,
    );

    const checkbox = screen.getByRole('checkbox', { name: 'Accept' });
    expect(checkbox.className).toContain('mt-2');
    expect(checkbox.getAttribute('aria-checked')).toBe('false');

    fireEvent.click(checkbox);

    expect(onCheckedChange).toHaveBeenCalledWith(true, expect.anything());
    expect(checkbox.getAttribute('aria-checked')).toBe('true');
  });
});
