import { fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type {
  Event,
  Match,
  Media,
  Team,
  TeamEventStatus,
} from '~/api/tba/read';
import EventTeamsTab from '~/components/tba/eventTeamsTab';

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

vi.mock('~/components/tba/eventRankTooltip', () => ({
  default: ({ rank }: { rank: number }) => <div>Rank {rank}</div>,
}));

vi.mock('~/components/tba/match/matchRows', () => ({
  default: ({ matches }: { matches: Match[] }) => (
    <ul aria-label="Matches">
      {matches.map((m) => (
        <li key={m.key}>{m.key}</li>
      ))}
    </ul>
  ),
}));

const event = {
  key: '2024casj',
  year: 2024,
  first_event_code: 'casj',
} as Event;

function match(key: string, red: string[], blue: string[]): Match {
  return {
    key,
    alliances: {
      red: { team_keys: red },
      blue: { team_keys: blue },
    },
  } as Match;
}

const team: Team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  name: 'NASA',
  city: 'San Jose',
  state_prov: 'California',
  country: 'USA',
  school_name: null,
  address: null,
  postal_code: null,
  gmaps_place_id: null,
  gmaps_url: null,
  lat: null,
  lng: null,
  location_name: null,
  website: null,
  rookie_year: 1999,
  motto: null,
};
const otherTeam: Team = {
  ...team,
  key: 'frc604',
  team_number: 604,
  nickname: 'Quixilver',
  city: 'Mountain View',
};
const photo: Media = {
  type: 'imgur',
  foreign_key: 'robot',
  team_keys: ['frc254'],
  preferred: true,
  direct_url: 'https://example.com/robot.png',
};
const avatar: Media = {
  type: 'avatar',
  foreign_key: '254',
  team_keys: ['frc254'],
  details: { base64Image: 'AAAA' },
};

function renderTeams(props: Partial<Parameters<typeof EventTeamsTab>[0]> = {}) {
  return render(
    <EventTeamsTab
      event={event}
      teams={[otherTeam, team]}
      matches={[]}
      media={[]}
      {...props}
    />,
  );
}

describe('EventTeamsTab', () => {
  test('shows teams in numerical order', () => {
    renderTeams();
    expect(
      screen
        .getAllByRole('listitem')
        .map((item) => within(item).getAllByRole('link')[0].textContent),
    ).toEqual(['254 - The Cheesy Poofs', '604 - Quixilver']);
  });

  test('links team names to the event year', () => {
    renderTeams({ event: { ...event, year: 2017 } });
    expect(
      screen
        .getByRole('link', { name: '254 - The Cheesy Poofs' })
        .getAttribute('href'),
    ).toBe('/team/254/2017');
  });

  test('renders historical teams without avatars', () => {
    renderTeams({ event: { ...event, year: 2017 } });
    expect(screen.queryByRole('img', { name: 'Team Avatar' })).toBeNull();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  test('shows available avatars when other teams have none', () => {
    renderTeams({ media: [avatar] });
    expect(screen.getAllByRole('img', { name: 'Team Avatar' })).toHaveLength(1);
  });

  test.each([
    ['number', '254'],
    ['name ignoring case and whitespace', '  CHEESY  '],
    ['city', 'san jose'],
    ['pit', 'a12'],
  ])('filters by %s', (_name, query) => {
    renderTeams({ statuses: { frc254: { pit_location: 'A12' } } });
    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: query },
    });
    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(
      screen.getByRole('link', { name: '254 - The Cheesy Poofs' }),
    ).toBeTruthy();
  });

  test.each([
    ['state', 'California'],
    ['state abbreviation', 'CA'],
    ['country', 'USA'],
  ])('filters by %s', (_name, query) => {
    renderTeams({
      teams: [team, { ...otherTeam, state_prov: 'London', country: 'UK' }],
    });
    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: query },
    });
    expect(screen.getAllByRole('listitem')).toHaveLength(1);
  });

  test('reports the filtered count', () => {
    renderTeams();
    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: '254' },
    });
    expect(screen.getByRole('status').textContent).toBe('1 of 2 teams');
  });

  test('clearing search restores all teams', () => {
    renderTeams();
    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: '254' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  test('shows an empty search message', () => {
    renderTeams();
    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: 'no match' },
    });
    expect(screen.getByText('No teams match your search')).toBeTruthy();
  });

  test('shows an empty event message', () => {
    renderTeams({ teams: [] });
    expect(screen.getByText('No teams listed')).toBeTruthy();
  });

  test('omits missing names without a dangling separator', () => {
    renderTeams({ teams: [{ ...team, nickname: '' }] });
    expect(screen.getByRole('link', { name: '254' })).toBeTruthy();
  });

  test('omits locations when all location fields are missing', () => {
    renderTeams({
      teams: [{ ...team, city: null, state_prov: null, country: null }],
    });
    expect(screen.getAllByRole('link')).toHaveLength(1);
  });

  test('preserves the location map link', () => {
    renderTeams();
    expect(
      screen
        .getByRole('link', { name: 'San Jose, CA, USA' })
        .getAttribute('href'),
    ).toBe('https://maps.google.com/?q=San%20Jose%2C%20California%2C%20USA');
  });

  test('links known pits to the event map', () => {
    renderTeams({ statuses: { frc254: { pit_location: 'A12' } } });
    expect(screen.getByRole('link', { name: 'A12' }).getAttribute('href')).toBe(
      'https://frc.nexus/en/event/2024casj/team/254/map',
    );
  });

  test('shows unknown pits when the event has pit data', () => {
    renderTeams({ statuses: { frc254: { pit_location: 'A12' } } });
    expect(screen.getByText('Pit —')).toBeTruthy();
  });

  test('shows plain pit text without an event code', () => {
    renderTeams({
      event: { ...event, first_event_code: null },
      statuses: { frc254: { pit_location: 'A12' } },
    });
    expect(screen.getByText('Pit A12')).toBeTruthy();
    expect(screen.queryByRole('link', { name: 'A12' })).toBeNull();
  });

  test('links teams without matches to the team page', () => {
    renderTeams({ matches: [match('2024casj_qm1', ['frc604'], [])] });
    expect(
      screen
        .getByRole('link', { name: '254 - The Cheesy Poofs' })
        .getAttribute('href'),
    ).toBe('/team/254/2024');
  });

  test('opens a dialog for teams with matches', async () => {
    renderTeams({ matches: [match('2024casj_qm1', ['frc254'], [])] });
    fireEvent.click(
      screen.getByRole('button', { name: '254 - The Cheesy Poofs' }),
    );
    expect(
      await screen.findByRole('dialog', {
        name: 'Team 254 — The Cheesy Poofs',
      }),
    ).toBeTruthy();
  });

  test('links the dialog title to the team page', async () => {
    renderTeams({ matches: [match('2024casj_qm1', ['frc254'], [])] });
    fireEvent.click(
      screen.getByRole('button', { name: '254 - The Cheesy Poofs' }),
    );
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog)
        .getByRole('link', { name: 'Team 254 — The Cheesy Poofs' })
        .getAttribute('href'),
    ).toBe('/team/254/2024');
  });

  test("shows the team's record from its matches in the dialog", async () => {
    const status = {
      qual: {
        ranking: {
          rank: 3,
          record: { wins: 8, losses: 3, ties: 0 },
          sort_orders: [],
        },
      },
    } satisfies TeamEventStatus;
    renderTeams({
      matches: [
        {
          key: '2024casj_qm1',
          comp_level: 'qm',
          winning_alliance: 'red',
          alliances: {
            red: { team_keys: ['frc254'], score: 10 },
            blue: { team_keys: ['frc604'], score: 5 },
          },
        } as Match,
        {
          key: '2024casj_qm2',
          comp_level: 'qm',
          winning_alliance: 'red',
          alliances: {
            red: { team_keys: ['frc604'], score: 10 },
            blue: { team_keys: ['frc254'], score: 5 },
          },
        } as Match,
      ],
      statuses: { frc254: status },
    });
    fireEvent.click(
      screen.getByRole('button', { name: '254 - The Cheesy Poofs' }),
    );
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('1-1-0')).toBeTruthy();
  });

  test("shows only the team's matches in the dialog", async () => {
    renderTeams({
      matches: [
        match('2024casj_qm1', ['frc254'], ['frc604']),
        match('2024casj_qm2', ['frc604'], []),
        match('2024casj_qm3', [], ['frc254']),
      ],
    });
    fireEvent.click(
      screen.getByRole('button', { name: '254 - The Cheesy Poofs' }),
    );
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog)
        .getAllByRole('listitem')
        .map((item) => item.textContent),
    ).toEqual(['2024casj_qm1', '2024casj_qm3']);
  });

  test('opens the selected robot photo', async () => {
    renderTeams({ media: [photo] });
    fireEvent.click(
      screen.getByRole('button', { name: 'View robot photo for team 254' }),
    );
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog)
        .getByRole('img', { name: 'Team 254 robot' })
        .getAttribute('src'),
    ).toBe('https://example.com/robot.png');
  });
});
