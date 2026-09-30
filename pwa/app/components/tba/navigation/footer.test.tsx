import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { renderToString } from 'react-dom/server';
import { Temporal } from 'temporal-polyfill';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { Footer } from '~/components/tba/navigation/footer';

const mocks = vi.hoisted(() => ({
  resolvedTheme: 'light' as 'light' | 'dark',
  setTheme: vi.fn<(theme: string) => void>(),
}));

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

vi.mock('~/lib/theme', () => ({
  useTheme: () => ({
    resolvedTheme: mocks.resolvedTheme,
    setTheme: mocks.setTheme,
  }),
}));

function themeToggle() {
  return screen.getByRole('button', { name: 'Toggle Theme' });
}

describe('Footer', () => {
  beforeEach(() => {
    mocks.resolvedTheme = 'light';
  });

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

  test('omits the render time and active theme on the server', () => {
    const html = renderToString(<Footer />);

    expect(html).not.toContain('Generated on');
    expect(html).toContain('data-mounted="false"');
    expect(html).not.toContain('data-active="true"');
  });

  test('marks the active theme and switches from light to dark', () => {
    render(<Footer />);

    const icons = themeToggle().querySelectorAll('svg');
    expect(icons[0].getAttribute('data-active')).toBe('true');
    expect(icons[1].getAttribute('data-active')).toBe('false');

    fireEvent.click(themeToggle());

    expect(mocks.setTheme).toHaveBeenCalledWith('dark');
  });

  test('switches from dark to light', () => {
    mocks.resolvedTheme = 'dark';
    render(<Footer />);

    fireEvent.click(themeToggle());

    expect(mocks.setTheme).toHaveBeenCalledWith('light');
  });
});
