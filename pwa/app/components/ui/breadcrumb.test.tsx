import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '~/components/ui/breadcrumb';

describe('Breadcrumb', () => {
  test('renders a labelled nav with a list of items', () => {
    render(
      <Breadcrumb>
        <BreadcrumbList className="group/list">
          <BreadcrumbItem className="group/item">
            <BreadcrumbLink href="/events" className="group/link">
              Events
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>2026casj</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>,
    );

    const nav = screen.getByRole('navigation', { name: 'breadcrumb' });
    expect(nav.getAttribute('data-slot')).toBe('breadcrumb');

    const list = screen.getByRole('list');
    expect(list.className).toContain('group/list');

    const link = screen.getByRole('link', { name: 'Events' });
    expect(link.getAttribute('href')).toBe('/events');
    expect(link.getAttribute('data-slot')).toBe('breadcrumb-link');
    expect(link.className).toContain('group/link');
    expect(link.className).toContain('hover:text-foreground');
    expect(link.closest('li')?.className).toContain('group/item');

    const separator = nav.querySelector('[data-slot="breadcrumb-separator"]');
    expect(separator?.getAttribute('aria-hidden')).toBe('true');
    expect(separator?.querySelector('svg')).not.toBeNull();
  });

  test('BreadcrumbLink renders through a custom element when given one', () => {
    render(
      <BreadcrumbLink
        render={<button type="button" aria-label="Back" />}
        onClick={() => undefined}
      >
        Back
      </BreadcrumbLink>,
    );

    const button = screen.getByRole('button', { name: 'Back' });
    expect(button.className).toContain('transition-colors');
  });

  test('BreadcrumbSeparator renders custom children instead of the chevron', () => {
    render(
      <ul>
        <BreadcrumbSeparator className="group/separator">/</BreadcrumbSeparator>
      </ul>,
    );

    const separator = screen.getByText('/');
    expect(separator.className).toContain('group/separator');
    expect(separator.querySelector('svg')).toBeNull();
  });

  test('BreadcrumbEllipsis renders an icon with hidden text', () => {
    render(<BreadcrumbEllipsis className="group/ellipsis" />);

    const more = screen.getByText('More');
    expect(more.className).toContain('sr-only');
    const ellipsis = more.parentElement;
    expect(ellipsis?.getAttribute('data-slot')).toBe('breadcrumb-ellipsis');
    expect(ellipsis?.getAttribute('aria-hidden')).toBe('true');
    expect(ellipsis?.className).toContain('group/ellipsis');
    expect(ellipsis?.querySelector('svg')).not.toBeNull();
  });
});

describe('BreadcrumbPage', () => {
  test('marks its content as the current page', () => {
    render(<BreadcrumbPage>Event</BreadcrumbPage>);

    expect(screen.getByText('Event').getAttribute('aria-current')).toBe('page');
  });

  test('renders its content as non-interactive text', () => {
    render(<BreadcrumbPage>Event</BreadcrumbPage>);

    expect(screen.queryByRole('link', { name: 'Event' })).toBeNull();
  });

  test('merges the given class name', () => {
    render(<BreadcrumbPage className="group/page">Event</BreadcrumbPage>);

    expect(screen.getByText('Event').className).toContain('group/page');
    expect(screen.getByText('Event').className).toContain('text-foreground');
  });
});
