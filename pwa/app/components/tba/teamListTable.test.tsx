import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { TeamSimple } from '~/api/tba/read';
import TeamListTable from '~/components/tba/teamListTable';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params: { teamNumber: string };
    to: string;
  }) => (
    <a href={to.replace('$teamNumber', params.teamNumber)} {...props}>
      {children}
    </a>
  ),
}));

describe('TeamListTable', () => {
  test('renders team rows with optional locations', () => {
    const teams: TeamSimple[] = [
      {
        key: 'frc254',
        team_number: 254,
        nickname: 'The Cheesy Poofs',
        name: 'NASA',
        city: 'San Jose',
        state_prov: 'CA',
        country: 'USA',
      },
      {
        key: 'frc9999',
        team_number: 9999,
        nickname: 'No City',
        name: 'None',
        city: null,
        state_prov: null,
        country: null,
      },
    ];
    render(<TeamListTable teams={teams} />);
    expect(screen.getByRole('link', { name: '254' })).toHaveProperty(
      'href',
      `${window.location.origin}/team/254/%7B-$year%7D`,
    );
    expect(screen.getByText('San Jose, CA, USA')).toBeTruthy();
    expect(screen.getByText('No City')).toBeTruthy();
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });
});
