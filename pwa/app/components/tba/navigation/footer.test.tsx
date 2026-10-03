import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { renderToString } from 'react-dom/server';
import { Temporal } from 'temporal-polyfill';
import { describe, expect, test, vi } from 'vitest';

import { Footer } from '~/components/tba/navigation/footer';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe('Footer', () => {
  test('links to internal pages and external sites', () => {
    render(<Footer />);

    expect(
      screen.getByRole('link', { name: 'About us' }).getAttribute('href'),
    ).toBe('/about');
    const github = screen.getByRole('link', { name: 'GitHub' });
    expect(github.getAttribute('href')).toBe(
      'https://github.com/the-blue-alliance/the-blue-alliance',
    );
    expect(github.getAttribute('target')).toBe('_blank');
    expect(github.querySelector('svg')).toBeTruthy();
    expect(
      screen.getByRole('link', { name: 'Blog' }).getAttribute('href'),
    ).toBe('https://blog.thebluealliance.com');
    // A separator between each of the nine links.
    expect(screen.getAllByText('/')).toHaveLength(8);
    expect(screen.getByAltText('AndyMark')).toBeTruthy();
  });

  test('shows the render time and commit after hydration', () => {
    vi.spyOn(Temporal.Now, 'zonedDateTimeISO').mockReturnValue(
      Temporal.ZonedDateTime.from('2026-04-23T16:05:00[UTC]'),
    );

    render(<Footer />);

    const credit = screen.getByText(/Data provided by the/);
    expect(credit.textContent).toContain(
      '. Generated on Apr 23, 2026, 4:05 PM',
    );
    const commit = credit.querySelector('a[href*="/commit/"]');
    expect(commit?.getAttribute('href')).toBe(
      `https://github.com/the-blue-alliance/the-blue-alliance/commit/${commit?.textContent}`,
    );
  });

  test('omits the render time on the server', () => {
    const html = renderToString(<Footer />);

    expect(html).not.toContain('Generated on');
  });
});
