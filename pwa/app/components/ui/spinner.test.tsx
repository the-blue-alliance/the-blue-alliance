import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Spinner } from '~/components/ui/spinner';

describe('Spinner', () => {
  test('renders an accessible loading indicator', () => {
    render(<Spinner className="size-8" />);

    const spinner = screen.getByRole('status', { name: 'Loading' });
    expect(spinner.getAttribute('class')).toContain('animate-spin');
    expect(spinner.getAttribute('class')).toContain('size-8');
  });
});
