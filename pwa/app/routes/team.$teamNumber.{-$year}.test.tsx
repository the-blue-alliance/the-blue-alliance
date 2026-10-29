import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/team.$teamNumber.{-$year}';

const team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  city: 'San Jose',
  state_prov: 'CA',
  postal_code: '95112',
  country: 'USA',
};

function load(year: string | undefined, responses: Record<string, unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id in responses
        ? Promise.resolve(responses[queryKey[0]._id])
        : Promise.reject(new Error('500')),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { teamNumber: '254', year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('team route loader', () => {
  test('loads a year the team competed in', async () => {
    await expect(
      load('2024', { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).resolves.toEqual({
      teamKey: 'frc254',
      year: 2024,
      avatarYear: 2024,
      team,
    });
  });

  test('uses the most recent active year for the avatar before 2018', async () => {
    await expect(
      load('2015', { getTeam: team, getTeamYearsParticipated: [2015, 2025] }),
    ).resolves.toMatchObject({ avatarYear: 2025 });
  });

  test('throws not-found for an invalid year', async () => {
    await expect(load('abc', {})).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found when the team fails to load', async () => {
    await expect(
      load('2024', { getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found for a requested year the team skipped', async () => {
    await expect(
      load('2020', { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('redirects to history when the team skipped the current season', async () => {
    await expect(
      load(undefined, { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({
      options: {
        to: '/team/$teamNumber/history',
        params: { teamNumber: '254' },
      },
    });
  });

  test('loads the page when the years-participated fetch fails', async () => {
    await expect(load('2020', { getTeam: team })).resolves.toMatchObject({
      year: 2020,
    });
  });

  test('tolerates failed socials and team statuses', async () => {
    await expect(
      load('2024', {
        getTeam: team,
        getTeamYearsParticipated: [2024],
        getTeamMediaByYear: [],
        getTeamMatchesByYear: [],
        getTeamAwardsByYear: [],
        getTeamEventsByYear: [],
        getTeamDistricts: [],
      }),
    ).resolves.toMatchObject({ year: 2024 });
  });

  test('loads the page when remapped robot data fails to load', async () => {
    await expect(
      load('2026', {
        getTeam: team,
        getTeamYearsParticipated: [2026],
        getTeamEventsByYear: [
          { key: '2026nhmm', remap_teams: { frc9997: 'frc254B' } },
        ],
      }),
    ).resolves.toMatchObject({ year: 2026 });
  });

  test('fetches the remapped robot status under its demo team', async () => {
    const ensureQueryData = vi.fn<
      (options: {
        queryKey: [{ _id: string; path?: Record<string, string> }];
      }) => Promise<unknown>
    >(({ queryKey }) =>
      Promise.resolve(
        {
          getTeam: team,
          getTeamYearsParticipated: [2026],
          getTeamEventsByYear: [
            { key: '2026nhmm', remap_teams: { frc9997: 'frc254B' } },
          ],
        }[queryKey[0]._id] ?? [],
      ),
    );

    await runLoader(Route, {
      params: { teamNumber: '254', year: '2026' },
      context: {
        queryClient: { ensureQueryData } as unknown as QueryClient,
        currentSeason: 2026,
      },
    });

    expect(
      ensureQueryData.mock.calls
        .map(([{ queryKey }]) => queryKey[0])
        .find(({ _id }) => _id === 'getTeamEventStatus')?.path,
    ).toEqual({ team_key: 'frc9997', event_key: '2026nhmm' });
  });

  test.each(['getEventMatches', 'getEventAlliances'])(
    'does not wait for %s',
    async (pendingId) => {
      const responses: Record<string, unknown> = {
        getTeam: team,
        getTeamYearsParticipated: [2026],
        getTeamEventsByYear: [
          {
            key: '2026nhmm',
            event_type: 99,
            remap_teams: { frc9997: 'frc254B' },
          },
        ],
      };
      const ensureQueryData = vi.fn<
        (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
      >(({ queryKey }) =>
        queryKey[0]._id === pendingId
          ? new Promise(() => {})
          : Promise.resolve(responses[queryKey[0]._id] ?? []),
      );

      await expect(
        runLoader(Route, {
          params: { teamNumber: '254', year: '2026' },
          context: {
            queryClient: { ensureQueryData } as unknown as QueryClient,
            currentSeason: 2026,
          },
        }),
      ).resolves.toMatchObject({ year: 2026 });
    },
  );
});

describe('team route loader prefetching', () => {
  async function startedQueries(responses: Record<string, unknown>) {
    const ensureQueryData = vi.fn<
      (options: {
        queryKey: [{ _id: string; path?: Record<string, unknown> }];
      }) => Promise<unknown>
    >(({ queryKey }) => Promise.resolve(responses[queryKey[0]._id] ?? []));
    await runLoader(Route, {
      params: { teamNumber: '254', year: '2026' },
      context: {
        queryClient: { ensureQueryData } as unknown as QueryClient,
        currentSeason: 2026,
      },
    });
    return ensureQueryData.mock.calls.map(([{ queryKey }]) => ({
      _id: queryKey[0]._id,
      path: queryKey[0].path,
    }));
  }

  test.each([
    {
      name: 'alliances for an offseason event',
      events: [{ key: '2026cc', event_type: 99 }],
      districts: [],
      expected: { _id: 'getEventAlliances', path: { event_key: '2026cc' } },
    },
    {
      name: 'district points for a district event',
      events: [{ key: '2026nhgrs', event_type: 1 }],
      districts: [],
      expected: {
        _id: 'getEventDistrictPoints',
        path: { event_key: '2026nhgrs' },
      },
    },
    {
      name: 'regional pool points for a regional',
      events: [{ key: '2026casj', event_type: 0 }],
      districts: [],
      expected: {
        _id: 'getRegionalChampsPoolPoints',
        path: { event_key: '2026casj' },
      },
    },
    {
      name: 'regional advancement when the team attends a regional',
      events: [{ key: '2026casj', event_type: 0 }],
      districts: [],
      expected: { _id: 'getRegionalAdvancement', path: { year: 2026 } },
    },
    {
      name: 'district rankings for the team district that year',
      events: [],
      districts: [
        { key: '2025ne', year: 2025 },
        { key: '2026ne', year: 2026 },
      ],
      expected: {
        _id: 'getDistrictRankings',
        path: { district_key: '2026ne' },
      },
    },
    {
      name: 'regional rankings when the team has no district that year',
      events: [],
      districts: [{ key: '2025ne', year: 2025 }],
      expected: { _id: 'getRegionalRankings', path: { year: 2026 } },
    },
  ])('starts $name', async ({ events, districts, expected }) => {
    const queries = await startedQueries({
      getTeam: team,
      getTeamYearsParticipated: [2026],
      getTeamEventsByYear: events,
      getTeamDistricts: districts,
    });

    expect(queries).toContainEqual(expected);
  });

  test('skips district points for a regional', async () => {
    const queries = await startedQueries({
      getTeam: team,
      getTeamYearsParticipated: [2026],
      getTeamEventsByYear: [{ key: '2026casj', event_type: 0 }],
    });

    expect(queries.map(({ _id }) => _id)).not.toContain(
      'getEventDistrictPoints',
    );
  });
});

describe('team route head', () => {
  test('titles the page with the team', () => {
    expect(runHead(Route, { loaderData: { team } })?.meta?.[0]).toEqual({
      title: 'The Cheesy Poofs - Team 254 - The Blue Alliance',
    });
  });

  test('describes the team location in structured data', () => {
    const head = runHead(Route, { loaderData: { team } });
    expect(
      JSON.parse(head?.scripts?.[0]?.children as string).location.address,
    ).toEqual({
      '@type': 'PostalAddress',
      addressLocality: 'San Jose',
      addressRegion: 'CA',
      postalCode: '95112',
      addressCountry: 'USA',
    });
  });

  test('describes a team with no postal code without printing null', () => {
    expect(
      runHead(Route, {
        loaderData: { team: { ...team, postal_code: null } },
      })?.meta?.[1],
    ).toEqual({
      name: 'description',
      content:
        'From San Jose, CA, USA. Team information, match results, and match videos from the FIRST Robotics Competition.',
    });
  });

  test('omits the location sentence for a team with no location', () => {
    expect(
      runHead(Route, {
        loaderData: {
          team: {
            ...team,
            city: null,
            state_prov: null,
            postal_code: null,
            country: null,
          },
        },
      })?.meta?.[1],
    ).toEqual({
      name: 'description',
      content:
        'Team information, match results, and match videos from the FIRST Robotics Competition.',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Team Information - The Blue Alliance',
    });
  });
});
