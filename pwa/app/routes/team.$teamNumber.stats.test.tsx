import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/team.$teamNumber.stats';

const team = { key: 'frc254', team_number: 254, nickname: 'The Cheesy Poofs' };

function load(responses: Record<string, unknown>) {
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
    params: { teamNumber: '254' },
    context: { queryClient },
  });
}

describe('team stats route loader', () => {
  test('loads the team despite failed awards, socials, and media', async () => {
    await expect(
      load({ getTeam: team, getTeamEvents: [] }),
    ).resolves.toMatchObject({ teamKey: 'frc254', team });
  });

  test('throws not-found when the team fails to load', async () => {
    await expect(load({ getTeamEvents: [] })).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the team events fail to load', async () => {
    await expect(load({ getTeam: team })).rejects.toMatchObject({
      isNotFound: true,
    });
  });
});

describe('team stats route head', () => {
  test('titles the page with the team', () => {
    expect(runHead(Route, { loaderData: { team } })?.meta?.[0]).toEqual({
      title: 'The Cheesy Poofs - Team 254 (Stats) - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Team Stats - The Blue Alliance',
    });
  });
});
