import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import type { TeamSimple } from '~/api/tba/read';
import TeamListTable from '~/components/tba/teamListTable';

vi.mock('@tanstack/react-router', () => import('~/testing/mocks/router'));

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
      `${window.location.origin}/team/254`,
    );
    expect(screen.getByText('San Jose, CA, USA')).toBeTruthy();
    expect(screen.getByText('No City')).toBeTruthy();
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });
});
