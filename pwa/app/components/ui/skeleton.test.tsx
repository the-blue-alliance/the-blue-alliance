import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Skeleton } from '~/components/ui/skeleton';

describe('Skeleton', () => {
  test('renders a pulsing placeholder with merged classes', () => {
    render(<Skeleton className="h-4 w-20" data-testid="skeleton" />);

    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton.getAttribute('data-slot')).toBe('skeleton');
    expect(skeleton.className).toContain('animate-pulse');
    expect(skeleton.className).toContain('h-4');
  });
});
