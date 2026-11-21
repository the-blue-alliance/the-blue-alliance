import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Separator } from '~/components/ui/separator';

describe('Separator', () => {
  test('defaults to horizontal', () => {
    render(<Separator className="mt-2" />);

    const separator = screen.getByRole('separator');
    expect(separator.getAttribute('data-slot')).toBe('separator');
    expect(separator.getAttribute('aria-orientation')).toBe('horizontal');
    expect(separator.className).toContain('mt-2');
  });

  test('supports vertical orientation', () => {
    render(<Separator orientation="vertical" />);

    expect(screen.getByRole('separator').getAttribute('aria-orientation')).toBe(
      'vertical',
    );
  });
});
