import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { District, Media, MediaAvatar, Team } from '~/api/tba/read';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';

vi.mock('~/components/tba/links', () => ({
  TeamLocationLink: ({ team }: { team: Team }) => (
    <a href="#map">{team.city}</a>
  ),
  DistrictLink: ({
    children,
    districtAbbreviation,
    year,
  }: {
    children: ReactNode;
    districtAbbreviation: string;
    year: number;
  }) => <a href={`/district/${districtAbbreviation}/${year}`}>{children}</a>,
}));

const team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  name: 'NASA Ames Research Center/Google&Bellarmine College Preparatory',
  school_name: 'Bellarmine College Preparatory',
  city: 'San Jose',
  state_prov: 'CA',
  country: 'USA',
  rookie_year: 1999,
} as Team;

const district: District = {
  abbreviation: 'ca',
  display_name: 'California',
  key: '2026ca',
  year: 2026,
  official_advancement_counts: { dcmp: 50, cmp: 20 },
};

describe('TeamPageTeamInfo', () => {
  test('renders team details, district, sponsors, and socials', async () => {
    render(
      <TeamPageTeamInfo
        team={team}
        maybeAvatar={
          {
            type: 'avatar',
            foreign_key: 'avatar_2026_frc254',
            details: { base64Image: 'AAAA' },
          } as MediaAvatar
        }
        socials={[
          {
            type: 'github-profile',
            foreign_key: 'team254',
            team_keys: ['frc254'],
          } as Media,
        ]}
        district={district}
        favoriteButton={<button>Favorite</button>}
      />,
    );
    expect(
      screen.getByRole('heading', { name: 'Team 254 - The Cheesy Poofs' }),
    ).toBeTruthy();
    expect(screen.getByRole('img', { name: 'Team Avatar' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Favorite' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'San Jose' })).toBeTruthy();
    expect(
      screen.getByRole('link', { name: 'California' }).getAttribute('href'),
    ).toBe('/district/ca/2026');
    expect(screen.getByText('Rookie Year: 1999')).toBeTruthy();
    for (const [name, href] of [
      ['FRC Events', 'https://frc-events.firstinspires.org/team/254'],
      ['Statbotics', 'https://www.statbotics.io/team/254'],
      ['Match13', 'https://www.match13.com/team/254'],
      ['team254', 'https://github.com/team254'],
    ]) {
      expect(screen.getByRole('link', { name }).getAttribute('href')).toBe(
        href,
      );
    }

    const trigger = screen.getByRole('button', {
      name: 'Bellarmine College Preparatory with 2 sponsors',
    });
    fireEvent.click(trigger);
    expect(await screen.findByText('NASA Ames Research Center')).toBeTruthy();
    expect(screen.getByText('Google')).toBeTruthy();
  });

  test('falls back to the school parsed from the team name without sponsors', () => {
    render(
      <TeamPageTeamInfo
        team={{ ...team, name: 'Some High School', school_name: null }}
        maybeAvatar={undefined}
        socials={[]}
      />,
    );
    expect(screen.queryByRole('img')).toBeNull();
    expect(screen.queryByText(/Part of the/)).toBeNull();
    expect(screen.getByText('Some High School')).toBeTruthy();
    expect(screen.queryByText(/sponsor/)).toBeNull();
  });

  test('the sponsor label has a single space before "sponsors"', () => {
    // HTML collapses a double space when rendered, so this checks textContent.
    render(
      <TeamPageTeamInfo team={team} maybeAvatar={undefined} socials={[]} />,
    );
    expect(
      screen.getByRole('button', {
        name: 'Bellarmine College Preparatory with 2 sponsors',
      }).textContent,
    ).toBe('Bellarmine College Preparatory with 2 sponsors');
  });
});
