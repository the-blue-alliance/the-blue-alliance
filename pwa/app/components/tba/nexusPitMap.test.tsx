import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { NexusMapPit, NexusPitMap } from '~/api/tba/read';
import NexusPitMapView from '~/components/tba/nexusPitMap';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to: _to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params: { teamNumber: string; year?: string };
    to: string;
  }) => (
    <a href={`/team/${params.teamNumber}/${params.year}`} {...props}>
      {children}
    </a>
  ),
}));

function pitMap(pits: Record<string, NexusMapPit>): NexusPitMap {
  return {
    size: { x: 400, y: 200 },
    pits,
    areas: {
      a0: {
        label: 'Machine shop',
        position: { x: 300, y: 50 },
        size: { x: 100, y: 100 },
      },
    },
    labels: {
      l0: {
        label: 'Practice field',
        position: { x: 300, y: 150 },
        size: { x: 100, y: 100 },
      },
    },
    arrows: {},
    walls: {},
  };
}

function pit(teamKey: string | null): NexusMapPit {
  return {
    position: { x: 50, y: 50 },
    size: { x: 100, y: 100 },
    team_key: teamKey,
  };
}

describe('NexusPitMap', () => {
  test('links the team in a pit to its team page for the year', () => {
    render(
      <NexusPitMapView pitMap={pitMap({ A1: pit('frc254') })} year={2026} />,
    );
    expect(screen.getByRole('link', { name: '254' }).getAttribute('href')).toBe(
      '/team/254/2026',
    );
  });

  test('shows a robot letter in the team number', () => {
    render(
      <NexusPitMapView pitMap={pitMap({ A1: pit('frc254b') })} year={2026} />,
    );
    expect(screen.getByRole('link', { name: '254B' })).toBeTruthy();
  });

  test('shows the team from the pit lookup when the map has none', () => {
    render(
      <NexusPitMapView
        pitMap={pitMap({ A1: pit(null) })}
        year={2026}
        teamsByPit={new Map([['A1', '604']])}
      />,
    );
    expect(screen.getByRole('link', { name: '604' })).toBeTruthy();
  });

  test('prefers the team named by the map over the pit lookup', () => {
    render(
      <NexusPitMapView
        pitMap={pitMap({ A1: pit('frc254') })}
        year={2026}
        teamsByPit={new Map([['A1', '604']])}
      />,
    );
    expect(screen.queryByRole('link', { name: '604' })).toBeNull();
  });

  test('shows the pit ID', () => {
    render(<NexusPitMapView pitMap={pitMap({ A1: pit(null) })} year={2026} />);
    expect(screen.getByText('A1')).toBeTruthy();
  });

  test('leaves an empty pit without a team link', () => {
    render(<NexusPitMapView pitMap={pitMap({ A1: pit(null) })} year={2026} />);
    expect(screen.queryByRole('link')).toBeNull();
  });

  test('shows area labels', () => {
    render(<NexusPitMapView pitMap={pitMap({})} year={2026} />);
    expect(screen.getByText('Machine shop')).toBeTruthy();
  });

  test('shows map labels', () => {
    render(<NexusPitMapView pitMap={pitMap({})} year={2026} />);
    expect(screen.getByText('Practice field')).toBeTruthy();
  });

  test('names the map for assistive technology', () => {
    render(<NexusPitMapView pitMap={pitMap({})} year={2026} />);
    expect(screen.getByRole('group', { name: 'Pit map' })).toBeTruthy();
  });
});
