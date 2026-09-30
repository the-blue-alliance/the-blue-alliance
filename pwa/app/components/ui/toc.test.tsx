import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { createRef } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
  TableOfContentsTitle,
} from '~/components/ui/toc';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    to: string;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe('TableOfContentsList', () => {
  test('has no padding without an indent', () => {
    render(<TableOfContentsList data-testid="list" />);

    const list = screen.getByTestId('list');
    expect(list.className).toContain('list-none');
    expect(list.className).not.toMatch(/pl-/);
  });

  test.each([
    [1, 'pl-4'],
    [2, 'pl-8'],
    [3, 'pl-12'],
    [4, 'pl-16'],
    [5, 'pl-20'],
    [9, 'pl-24'],
  ])('indent %s pads with %s', (indent, expected) => {
    render(<TableOfContentsList indent={indent} data-testid="list" />);

    expect(screen.getByTestId('list').className).toContain(expected);
  });

  test('forwards the ref and merges classes', () => {
    const ref = createRef<HTMLUListElement>();
    render(<TableOfContentsList ref={ref} className="group/list" />);

    expect(ref.current?.className).toContain('group/list');
  });
});

describe('TableOfContentsTitle', () => {
  test('renders a bold list item', () => {
    const ref = createRef<HTMLLIElement>();
    render(
      <ul>
        <TableOfContentsTitle ref={ref} className="group/title">
          Contents
        </TableOfContentsTitle>
      </ul>,
    );

    expect(ref.current).toBe(screen.getByText('Contents'));
    expect(ref.current?.className).toContain('group/title');
    expect(ref.current?.className).toContain('font-medium');
  });
});

describe('TableOfContentsItem', () => {
  test('has no margin without an indent', () => {
    render(
      <ul>
        <TableOfContentsItem>Item</TableOfContentsItem>
      </ul>,
    );

    expect(screen.getByText('Item').className).not.toMatch(/ml-/);
  });

  test.each([
    [1, 'ml-4'],
    [2, 'ml-8'],
    [3, 'ml-12'],
    [4, 'ml-16'],
    [5, 'ml-20'],
    [6, 'ml-24'],
  ])('indent %s offsets with %s', (indent, expected) => {
    render(
      <ul>
        <TableOfContentsItem indent={indent}>Item</TableOfContentsItem>
      </ul>,
    );

    expect(screen.getByText('Item').className).toContain(expected);
  });

  test('forwards the ref and merges classes', () => {
    const ref = createRef<HTMLLIElement>();
    render(
      <ul>
        <TableOfContentsItem ref={ref} className="group/item">
          Item
        </TableOfContentsItem>
      </ul>,
    );

    expect(ref.current?.className).toContain('group/item');
  });
});

describe('TableOfContentsLink', () => {
  test('renders an inactive link in muted text', () => {
    render(<TableOfContentsLink to="/events">Events</TableOfContentsLink>);

    const link = screen.getByRole('link', { name: 'Events' });
    expect(link.getAttribute('href')).toBe('/events');
    expect(link.className).toContain('text-muted-foreground');
    expect(link.className).not.toContain('font-bold');
  });

  test('renders an active link in bold and merges classes', () => {
    const ref = createRef<HTMLAnchorElement>();
    render(
      <TableOfContentsLink
        ref={ref}
        to="/teams"
        isActive
        className="group/link"
      >
        Teams
      </TableOfContentsLink>,
    );

    const link = screen.getByRole('link', { name: 'Teams' });
    expect(ref.current).toBe(link);
    expect(link.className).toContain('font-bold');
    expect(link.className).toContain('group/link');
  });
});
