import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { YearSelector } from '~/components/tba/yearSelector';

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

describe('YearSelector', () => {
  test('lists year options and marks the current one', async () => {
    render(
      <YearSelector
        currentLabel="2026"
        triggerClassName="trigger"
        contentClassName="content"
        options={[
          { label: '2026', to: '/team/254/2026', isCurrent: true },
          { label: '2025', to: '/team/254/2025' },
        ]}
      />,
    );
    const trigger = screen.getByRole('button', { name: '2026' });
    expect(trigger.className).toContain('trigger');

    fireEvent.click(trigger);

    const current = await screen.findByRole('menuitem', { name: '2026' });
    const other = screen.getByRole('menuitem', { name: '2025' });
    expect(current.getAttribute('href')).toBe('/team/254/2026');
    expect(other.getAttribute('href')).toBe('/team/254/2025');
    expect(current.querySelector('svg')?.getAttribute('class')).not.toContain(
      'invisible',
    );
    expect(other.querySelector('svg')?.getAttribute('class')).toContain(
      'invisible',
    );
  });
});
