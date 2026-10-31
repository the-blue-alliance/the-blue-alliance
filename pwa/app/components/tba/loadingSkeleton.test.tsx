import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import LoadingSkeleton from '~/components/tba/loadingSkeleton';

describe('LoadingSkeleton', () => {
  test('announces what is loading', () => {
    render(<LoadingSkeleton label="Loading rank" />);

    expect(screen.getByRole('status', { name: 'Loading rank' })).toBeTruthy();
  });
});
