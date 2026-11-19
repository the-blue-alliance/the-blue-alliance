import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type {
  Event,
  Match,
  Media,
  NexusPitMap,
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

const relatedEvents: Record<
  string,
  {
    pitMap: NexusPitMap;
    statuses: Record<string, Partial<TeamEventStatus>>;
  }
> = {};

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getEventNexusInfoOptions: ({ path }: { path: { event_key: string } }) => ({
    queryKey: ['nexus', path.event_key],
    queryFn: () =>
      Promise.resolve({ pit_map: relatedEvents[path.event_key].pitMap }),
  }),
  getEventTeamsStatusesOptions: ({
    path,
  }: {
    path: { event_key: string };
  }) => ({
    queryKey: ['statuses', path.event_key],
    queryFn: () => Promise.resolve(relatedEvents[path.event_key].statuses),
  }),
}));

vi.mock('~/api/colors/@tanstack/react-query.gen', () => ({
  getEventColorsOptions: ({ path }: { path: { eventKey: string } }) => ({
    queryKey: ['colors', path.eventKey],
    queryFn: () => Promise.resolve({ teams: {} }),
  }),
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

const pitMap: NexusPitMap = {
  size: { x: 200, y: 100 },
  pits: {
    A1: {
      position: { x: 50, y: 50 },
      size: { x: 100, y: 100 },
      team_key: null,
    },
    A2: {
      position: { x: 150, y: 50 },
      size: { x: 100, y: 100 },
      team_key: null,
    },
  },
  areas: {},
  labels: {},
  arrows: {},
  walls: {},
};

function renderTeams(props: Partial<Parameters<typeof EventTeamsTab>[0]> = {}) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <EventTeamsTab
        event={event}
        teams={[otherTeam, team]}
        matches={[]}
        media={[]}
        {...props}
      />
    </QueryClientProvider>,
  );
}

async function openPitMap() {
  fireEvent.click(screen.getByRole('button', { name: 'Pit map' }));
  return screen.findByRole('group', { name: 'Pit map' });
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
    expect(screen.queryByRole('img', { name: /Team Avatar/ })).toBeNull();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  test('shows available avatars when other teams have none', () => {
    renderTeams({ media: [avatar] });
    expect(screen.getAllByRole('img', { name: 'Team Avatar' })).toHaveLength(1);
  });

  test('shows the default avatar for teams without one when others have avatars', () => {
    renderTeams({ media: [avatar] });
    expect(
      screen.getAllByRole('img', { name: 'Default Team Avatar' }),
    ).toHaveLength(1);
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

  describe('pit map', () => {
    test('offers the pit map when the event has one', () => {
      renderTeams({ pitMap });
      expect(screen.getByRole('button', { name: 'Pit map' })).toBeTruthy();
    });

    test('hides the pit map button without a pit map', () => {
      renderTeams();
      expect(screen.queryByRole('button', { name: 'Pit map' })).toBeNull();
    });

    test('opens the pit map in a dialog', async () => {
      renderTeams({ pitMap });
      const map = await openPitMap();
      expect(within(screen.getByRole('dialog')).getByRole('group')).toBe(map);
    });

    test('labels pits with the teams assigned to them', async () => {
      renderTeams({
        pitMap,
        statuses: {
          frc254: { pit_location: 'A1' },
          frc604: { pit_location: 'A2' },
        },
      });
      const map = await openPitMap();
      expect(
        within(map)
          .getAllByRole('link')
          .map((link) => link.textContent),
      ).toEqual(['254', '604']);
    });

    test('leaves pits unlabeled when a team pit is not on the map', async () => {
      renderTeams({
        pitMap,
        statuses: {
          frc254: { pit_location: 'A1' },
          frc604: { pit_location: 'C33' },
        },
      });
      const map = await openPitMap();
      expect(within(map).queryAllByRole('link')).toEqual([]);
    });

    test('labels pits with teams from a related event on the same map', async () => {
      relatedEvents['2024casj2'] = {
        pitMap,
        statuses: { frc1678: { pit_location: 'A2' } },
      };
      renderTeams({ pitMap, relatedEventKeys: ['2024casj2'] });
      const map = await openPitMap();
      expect(
        await within(map).findByRole('link', { name: '1678' }),
      ).toBeTruthy();
    });

    test('ignores teams from a related event whose map places pits elsewhere', async () => {
      relatedEvents['2024casj2'] = {
        pitMap,
        statuses: { frc1678: { pit_location: 'A2' } },
      };
      relatedEvents['2024casj3'] = {
        pitMap: {
          ...pitMap,
          pits: {
            ...pitMap.pits,
            A2: { ...pitMap.pits.A2, position: { x: 150, y: 150 } },
          },
        },
        statuses: { frc971: { pit_location: 'A1' } },
      };
      renderTeams({ pitMap, relatedEventKeys: ['2024casj2', '2024casj3'] });
      const map = await openPitMap();
      await within(map).findByRole('link', { name: '1678' });
      expect(within(map).queryByRole('link', { name: '971' })).toBeNull();
    });

    test('links to the event map on Nexus', async () => {
      renderTeams({ pitMap });
      await openPitMap();
      expect(
        screen
          .getByRole('link', { name: 'Pit map data from frc.nexus' })
          .getAttribute('href'),
      ).toBe('https://frc.nexus/en/event/2024casj/map');
    });
  });

  describe('with remapped teams', () => {
    const remapEvent = {
      ...event,
      remap_teams: { frc9990: 'frc254B' },
    } as Event;
    const placeholderTeam: Team = {
      ...team,
      key: 'frc9990',
      team_number: 9990,
      nickname: 'Off-Season Demo Team 9990',
    };

    test('lists a remapped robot under its real key', () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
      });
      expect(
        screen.getByRole('link', { name: '254B - The Cheesy Poofs' }),
      ).toBeTruthy();
    });

    test('hides the placeholder team for a remapped robot', () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
      });
      expect(screen.queryByRole('link', { name: /9990/ })).toBeNull();
    });

    test('lists a remapped robot after its main team', () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
      });
      expect(
        screen
          .getAllByRole('listitem')
          .map((item) => within(item).getAllByRole('link')[0].textContent),
      ).toEqual([
        '254 - The Cheesy Poofs',
        '254B - The Cheesy Poofs',
        '604 - Quixilver',
      ]);
    });

    test('links a remapped robot to its main team page', () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
      });
      expect(
        screen
          .getByRole('link', { name: '254B - The Cheesy Poofs' })
          .getAttribute('href'),
      ).toBe('/team/254/2024');
    });

    test("shows the remapped robot's matches in its dialog", async () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
        matches: [
          match('2024casj_qm1', ['frc254'], ['frc604']),
          match('2024casj_qm2', ['frc254B'], []),
        ],
      });
      fireEvent.click(
        screen.getByRole('button', { name: '254B - The Cheesy Poofs' }),
      );
      const dialog = await screen.findByRole('dialog');
      expect(
        within(dialog)
          .getAllByRole('listitem')
          .map((item) => item.textContent),
      ).toEqual(['2024casj_qm2']);
    });

    test("shows the remapped robot's status from the placeholder key", async () => {
      renderTeams({
        event: remapEvent,
        teams: [otherTeam, team, placeholderTeam],
        matches: [match('2024casj_qm1', ['frc254B'], [])],
        statuses: {
          frc9990: {
            qual: {
              ranking: {
                rank: 12,
                record: { wins: 1, losses: 0, ties: 0 },
                sort_orders: [],
              },
            },
          },
        },
      });
      fireEvent.click(
        screen.getByRole('button', { name: '254B - The Cheesy Poofs' }),
      );
      const dialog = await screen.findByRole('dialog');
      expect(within(dialog).getByText('Rank 12')).toBeTruthy();
    });
  });
});
