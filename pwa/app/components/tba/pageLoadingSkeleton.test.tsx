import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';

import PageLoadingSkeleton from '~/components/tba/pageLoadingSkeleton';

test('announces that the page is loading', () => {
  render(<PageLoadingSkeleton />);

  expect(screen.getByRole('status', { name: 'Loading page' })).toBeTruthy();
});
