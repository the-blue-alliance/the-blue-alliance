import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { Match, Team } from '~/api/tba/read';
import ScoutingTab from '~/components/tba/scoutingTab';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
}));

vi.mock('~/components/tba/scoutingExport', () => ({
  default: ({
    title,
    csvData,
    filename,
  }: {
    title: string;
    csvData: string;
    filename: string;
  }) => (
    <section aria-label={title} data-filename={filename}>
      <pre>{csvData}</pre>
    </section>
  ),
}));

const team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  city: 'San Jose',
  state_prov: 'CA',
  country: 'USA',
} as Team;

const match = {
  key: '2026miket_qm1',
  event_key: '2026miket',
  comp_level: 'qm',
  set_number: 1,
  match_number: 1,
  time: null,
  alliances: {
    red: { team_keys: ['frc254', 'frc1', 'frc2'], score: 10 },
    blue: { team_keys: ['frc3', 'frc4', 'frc5'], score: 20 },
  },
} as unknown as Match;

function exportSection(name: string) {
  return screen.getByRole('region', { name });
}

describe('ScoutingTab', () => {
  test('offers team, schedule, and COPR exports', () => {
    render(
      <ScoutingTab
        teams={[team]}
        media={[]}
        matches={[match]}
        eventKey="2026miket"
        coprs={{ totalPoints: { frc254: 12.5 } }}
      />,
    );
    expect(
      screen.getByRole('link', { name: 'the API' }).getAttribute('href'),
    ).toBe('/apidocs/v3');

    const teams = exportSection('Team List');
    expect(teams.dataset.filename).toBe('2026miket_teams.csv');
    expect(teams.textContent).toContain('team_number,team_name');
    expect(teams.textContent).toContain('254,The Cheesy Poofs');

    expect(exportSection('Match Schedule').dataset.filename).toBe(
      '2026miket_schedule.csv',
    );
    expect(exportSection('Match Schedule').textContent).toContain(
      '2026miket_qm1',
    );
    expect(exportSection('Flat Match Schedule').dataset.filename).toBe(
      '2026miket_flat_schedule.csv',
    );
    const coprs = exportSection('Component OPRs');
    expect(coprs.dataset.filename).toBe('2026miket_coprs.csv');
    expect(coprs.textContent).toContain('totalPoints');
  });

  test('omits the COPR export without COPRs', () => {
    render(
      <ScoutingTab teams={[]} media={[]} matches={[]} eventKey="2026miket" />,
    );
    expect(screen.queryByRole('region', { name: 'Component OPRs' })).toBeNull();
    expect(screen.getAllByRole('region')).toHaveLength(3);
  });
});
