import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { BreadcrumbPage } from '~/components/ui/breadcrumb';

describe('BreadcrumbPage', () => {
  test('marks its content as the current page', () => {
    render(<BreadcrumbPage>Event</BreadcrumbPage>);

    expect(screen.getByText('Event').getAttribute('aria-current')).toBe('page');
  });

  test('renders its content as non-interactive text', () => {
    render(<BreadcrumbPage>Event</BreadcrumbPage>);

    expect(screen.queryByRole('link', { name: 'Event' })).toBeNull();
  });
});
