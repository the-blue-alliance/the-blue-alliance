import type { QueryClient } from '@tanstack/react-query';
import { Temporal } from 'temporal-polyfill';
import { describe, expect, test, vi } from 'vitest';

import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/team.$teamNumber.history';

const team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  city: 'San Jose',
  state_prov: 'CA',
  postal_code: '95112',
  country: 'USA',
};

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

describe('team history route loader', () => {
  test('loads the team despite failed years, socials, and media', async () => {
    await expect(load({ getTeam: team, getTeamHistory: {} })).resolves.toEqual({
      teamKey: 'frc254',
      mediaYear: expect.any(Number),
      team,
    });
  });

  test('resolves mediaYear from the current year', async () => {
    vi.spyOn(Temporal.Now, 'plainDateISO').mockReturnValueOnce(
      Temporal.PlainDate.from('2026-03-01'),
    );
    await expect(load({ getTeam: team, getTeamHistory: {} })).resolves.toEqual({
      teamKey: 'frc254',
      mediaYear: 2026,
      team,
    });
  });

  test('prefetches media for the current year', async () => {
    vi.spyOn(Temporal.Now, 'plainDateISO').mockReturnValueOnce(
      Temporal.PlainDate.from('2026-03-01'),
    );
    const ensureQueryData = vi
      .fn<() => Promise<unknown>>()
      .mockResolvedValue({});
    const queryClient = { ensureQueryData } as unknown as QueryClient;
    await runLoader(Route, {
      params: { teamNumber: '254' },
      context: { queryClient },
    });
    expect(ensureQueryData).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: expect.arrayContaining([
          expect.objectContaining({
            _id: 'getTeamMediaByYear',
            path: { team_key: 'frc254', year: 2026 },
          }),
        ]),
      }),
    );
  });

  test('throws not-found when the team fails to load', async () => {
    await expect(load({ getTeamHistory: {} })).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the team history fails to load', async () => {
    await expect(load({ getTeam: team })).rejects.toMatchObject({
      isNotFound: true,
    });
  });
});

describe('team history route head', () => {
  test('titles the page with the team', () => {
    expect(runHead(Route, { loaderData: { team } })?.meta?.[0]).toEqual({
      title: 'The Cheesy Poofs - Team 254 (History) - The Blue Alliance',
    });
  });

  test('describes where the team is from', () => {
    expect(runHead(Route, { loaderData: { team } })?.meta?.[1]).toEqual({
      name: 'description',
      content:
        'From San Jose, CA 95112, USA. Team information, match results, and match videos from the FIRST Robotics Competition.',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Team History - The Blue Alliance',
    });
  });
});
