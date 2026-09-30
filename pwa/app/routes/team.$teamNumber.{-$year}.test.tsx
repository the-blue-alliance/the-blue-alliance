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
    ).resolves.toEqual({ teamKey: 'frc254', year: 2024, team });
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

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Team Information - The Blue Alliance',
    });
  });
});
