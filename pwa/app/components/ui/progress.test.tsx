import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Progress } from '~/components/ui/progress';

describe('Progress', () => {
  test('renders a progressbar with the given value and class on the track', () => {
    render(<Progress value={40} className="h-4" />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar.getAttribute('aria-valuenow')).toBe('40');
    expect(progressbar.getAttribute('data-slot')).toBe('progress');

    const track = progressbar.querySelector('[data-slot="progress-track"]');
    expect(track?.className).toContain('h-4');
    expect(
      progressbar.querySelector('[data-slot="progress-indicator"]'),
    ).not.toBeNull();
  });
});
